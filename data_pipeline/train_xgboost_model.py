"""
Trains an XGBoost regressor to predict tomorrow's WBGT from today's
conditions, using the CSV produced by build_historical_dataset.py.

Usage:
    python train_xgboost_model.py --input historical_wbgt_dataset.csv

Outputs:
    model.json              -- the trained XGBoost model (portable format)
    model_metadata.json     -- feature list + which columns are categorical,
                                needed to reconstruct the same input shape
                                when serving predictions later

Evaluation is always reported against a "persistence" baseline (predicting
tomorrow's WBGT = today's WBGT) -- for day-to-day weather, that naive
baseline is genuinely hard to beat, and a model that doesn't beat it isn't
adding value yet. This is the single most important number in the output.
"""

import argparse
import json

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

NUMERIC_FEATURES = [
    "latitude", "longitude", "month",
    "temperature_c", "relative_humidity_pct", "wind_speed_ms", "solar_radiation_kwh_m2",
    "wbgt_c", "heat_index_c", "wbgt_lag1", "wbgt_roll3",
    "day_of_year_sin", "day_of_year_cos",
]
CATEGORICAL_FEATURES = ["district"]
TARGET = "wbgt_next_day"


def load_and_clean(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, parse_dates=["date"])
    before = len(df)
    # wbgt_lag1 is blank on each district's first day, wbgt_next_day is
    # blank on each district's last day -- both are unusable rows for
    # training, not a sign of a bug.
    df = df.dropna(subset=["wbgt_lag1", TARGET]).reset_index(drop=True)
    print(f"Loaded {before} rows, {len(df)} usable after dropping edge-of-series rows.")
    return df


def add_cyclical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encodes day_of_year as sin/cos instead of a raw 1-365 integer, so the
    model sees Dec 31 -> Jan 1 as adjacent (a small step) rather than a
    365-unit jump, which a raw integer would otherwise imply.
    """
    df = df.copy()
    radians = 2 * np.pi * df["day_of_year"] / 365.0
    df["day_of_year_sin"] = np.sin(radians)
    df["day_of_year_cos"] = np.cos(radians)
    return df


def chronological_split(df: pd.DataFrame, test_fraction: float):
    """
    Splits by date, not randomly -- the last `test_fraction` of dates become
    the test set. A random split would leak information (via wbgt_lag1 /
    wbgt_roll3) between adjacent days and overstate how good the model is.
    """
    df = df.sort_values("date")
    cutoff = df["date"].quantile(1 - test_fraction, interpolation="nearest")
    train_df = df[df["date"] < cutoff]
    test_df = df[df["date"] >= cutoff]
    print(f"Chronological split at {cutoff.date()}: {len(train_df)} train rows, {len(test_df)} test rows.")
    return train_df, test_df


def prepare_features(df: pd.DataFrame):
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()
    for col in CATEGORICAL_FEATURES:
        X[col] = X[col].astype("category")
    y = df[TARGET]
    return X, y


def persistence_baseline_metrics(test_df: pd.DataFrame) -> dict:
    """Naive baseline: predict tomorrow's WBGT = today's WBGT."""
    y_true = test_df[TARGET]
    y_pred = test_df["wbgt_c"]
    return _metrics(y_true, y_pred)


def _metrics(y_true, y_pred) -> dict:
    return {
        "mae": round(mean_absolute_error(y_true, y_pred), 3),
        "rmse": round(mean_squared_error(y_true, y_pred) ** 0.5, 3),
        "r2": round(r2_score(y_true, y_pred), 3),
    }


def train_model(X_train, y_train, model_cls=None, **model_kwargs):
    """
    model_cls is injectable for testing (so tests don't require xgboost to
    be installed). Defaults to xgboost.XGBRegressor with categorical
    support enabled -- this is what actually runs in production use.
    """
    if model_cls is None:
        import xgboost as xgb
        model_cls = xgb.XGBRegressor
        defaults = dict(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            tree_method="hist",
            enable_categorical=True,
            random_state=42,
        )
        defaults.update(model_kwargs)
        model_kwargs = defaults

    model = model_cls(**model_kwargs)
    model.fit(X_train, y_train)
    return model


def evaluate_model(model, X_test, y_test) -> dict:
    y_pred = model.predict(X_test)
    return _metrics(y_test, y_pred)


def print_feature_importance(model, feature_names, top_n=10):
    if not hasattr(model, "feature_importances_"):
        return
    pairs = sorted(zip(feature_names, model.feature_importances_), key=lambda p: -p[1])
    print("\nTop feature importances:")
    for name, score in pairs[:top_n]:
        print(f"  {name:<25} {score:.4f}")


def try_shap_summary(model, X_sample):
    """Optional -- skips gracefully if shap isn't installed (pip install shap to enable)."""
    try:
        import shap
    except ImportError:
        print("\n(shap not installed -- skipping explainability summary. `pip install shap` to enable.)")
        return
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)
    mean_abs = np.abs(shap_values).mean(axis=0)
    pairs = sorted(zip(X_sample.columns, mean_abs), key=lambda p: -p[1])
    print("\nSHAP mean |impact| on prediction (top 10):")
    for name, val in pairs[:10]:
        print(f"  {name:<25} {val:.4f}")


def save_metadata(feature_columns, categorical_columns, path="model_metadata.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "feature_columns": feature_columns,
            "categorical_columns": categorical_columns,
            "target": TARGET,
        }, f, indent=2)
    print(f"Wrote {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--test-fraction", type=float, default=0.2)
    parser.add_argument("--model-output", default="model.json")
    args = parser.parse_args()

    df = load_and_clean(args.input)
    df = add_cyclical_features(df)
    train_df, test_df = chronological_split(df, args.test_fraction)

    X_train, y_train = prepare_features(train_df)
    X_test, y_test = prepare_features(test_df)

    baseline = persistence_baseline_metrics(test_df)
    print(f"\nPersistence baseline (predict tomorrow = today): {baseline}")

    model = train_model(X_train, y_train)
    result = evaluate_model(model, X_test, y_test)
    print(f"XGBoost model:                                    {result}")

    if result["mae"] < baseline["mae"]:
        improvement = round((1 - result["mae"] / baseline["mae"]) * 100, 1)
        print(f"\n-> Model beats the naive baseline by {improvement}% lower MAE.")
    else:
        print("\n-> Model did NOT beat the naive baseline -- more data, tuning, or "
              "different features are needed before this is worth deploying.")

    print_feature_importance(model, X_train.columns.tolist())
    try_shap_summary(model, X_test.sample(min(200, len(X_test)), random_state=42))

    model.save_model(args.model_output)
    print(f"\nWrote {args.model_output}")
    save_metadata(NUMERIC_FEATURES + CATEGORICAL_FEATURES, CATEGORICAL_FEATURES)


if __name__ == "__main__":
    main()
