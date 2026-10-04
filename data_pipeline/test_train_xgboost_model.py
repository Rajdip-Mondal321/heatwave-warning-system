import json
import os
import tempfile

import numpy as np
import pandas as pd

import train_xgboost_model as trainer


class DummyModel:
    """Stands in for xgboost.XGBRegressor so these tests don't require
    xgboost to be installed -- it implements the same fit/predict/
    feature_importances_ surface the real script relies on."""

    def fit(self, X, y):
        self._mean = float(y.mean())
        self.feature_importances_ = np.ones(len(X.columns)) / len(X.columns)
        return self

    def predict(self, X):
        return np.full(len(X), self._mean)


def _make_sample_csv(path, n_days=10, districts=("Kolkata", "Delhi")):
    rows = []
    for district in districts:
        wbgt = 28.0
        for day in range(n_days):
            date = pd.Timestamp("2024-05-01") + pd.Timedelta(days=day)
            wbgt += 0.3  # gentle warming trend, easy to reason about
            rows.append({
                "district": district, "state": "S", "latitude": 20.0, "longitude": 80.0,
                "date": date.date().isoformat(), "month": date.month, "day_of_year": date.dayofyear,
                "temperature_c": 30 + day * 0.2, "relative_humidity_pct": 60,
                "wind_speed_ms": 2.0, "solar_radiation_kwh_m2": 18.0,
                "wbgt_c": round(wbgt, 2), "heat_index_c": round(wbgt + 2, 2),
                "wbgt_risk_band": "High",
                "wbgt_lag1": "" if day == 0 else round(wbgt - 0.3, 2),
                "wbgt_roll3": round(wbgt, 2),
                "wbgt_next_day": "" if day == n_days - 1 else round(wbgt + 0.3, 2),
            })
    pd.DataFrame(rows).to_csv(path, index=False)


def test_load_and_clean_drops_edge_rows():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "sample.csv")
        _make_sample_csv(path, n_days=10, districts=("Kolkata", "Delhi"))
        df = trainer.load_and_clean(path)
        # 2 districts x 10 days = 20 rows, minus 1 first + 1 last row per district = 16
        assert len(df) == 16
        assert df["wbgt_lag1"].isna().sum() == 0
        assert df[trainer.TARGET].isna().sum() == 0


def test_cyclical_features_are_bounded():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "sample.csv")
        _make_sample_csv(path)
        df = trainer.add_cyclical_features(trainer.load_and_clean(path))
        assert df["day_of_year_sin"].between(-1, 1).all()
        assert df["day_of_year_cos"].between(-1, 1).all()


def test_chronological_split_has_no_future_leakage():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "sample.csv")
        _make_sample_csv(path, n_days=20)
        df = trainer.add_cyclical_features(trainer.load_and_clean(path))
        df["date"] = pd.to_datetime(df["date"])
        train_df, test_df = trainer.chronological_split(df, test_fraction=0.2)
        assert train_df["date"].max() < test_df["date"].min() or train_df["date"].max() == test_df["date"].min()
        assert len(train_df) + len(test_df) == len(df)


def test_persistence_baseline_matches_manual_calc():
    df = pd.DataFrame({"wbgt_c": [30.0, 32.0], "wbgt_next_day": [31.0, 33.0]})
    result = trainer.persistence_baseline_metrics(df)
    # both days are off by exactly 1.0 -> MAE should be 1.0
    assert result["mae"] == 1.0


def test_prepare_features_marks_district_as_category():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "sample.csv")
        _make_sample_csv(path)
        df = trainer.add_cyclical_features(trainer.load_and_clean(path))
        X, y = trainer.prepare_features(df)
        assert str(X["district"].dtype) == "category"
        assert len(X) == len(y)


def test_train_and_evaluate_with_dummy_model():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "sample.csv")
        _make_sample_csv(path, n_days=15)
        df = trainer.add_cyclical_features(trainer.load_and_clean(path))
        df["date"] = pd.to_datetime(df["date"])
        train_df, test_df = trainer.chronological_split(df, test_fraction=0.3)
        X_train, y_train = trainer.prepare_features(train_df)
        X_test, y_test = trainer.prepare_features(test_df)

        model = trainer.train_model(X_train, y_train, model_cls=DummyModel)
        result = trainer.evaluate_model(model, X_test, y_test)
        assert "mae" in result and "rmse" in result and "r2" in result


def test_save_metadata_writes_expected_json():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "meta.json")
        trainer.save_metadata(["a", "b"], ["a"], path=path)
        with open(path) as f:
            data = json.load(f)
        assert data["feature_columns"] == ["a", "b"]
        assert data["categorical_columns"] == ["a"]
        assert data["target"] == trainer.TARGET


if __name__ == "__main__":
    import sys
    current_module = sys.modules[__name__]
    passed, failed = 0, 0
    for name in dir(current_module):
        if name.startswith("test_"):
            fn = getattr(current_module, name)
            try:
                fn()
                print(f"PASS  {name}")
                passed += 1
            except AssertionError as e:
                print(f"FAIL  {name}: {e}")
                failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
