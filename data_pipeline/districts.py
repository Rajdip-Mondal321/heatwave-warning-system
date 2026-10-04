"""
Shared district list.

Both main.py (the live API) and build_historical_dataset.py (the training
data pipeline) should import DISTRICTS from here, so the two never drift
out of sync. Replace/extend this with your complete Indian district dataset
when ready -- everything downstream (weather fetching, WBGT calculation,
dataset building) works unchanged regardless of list length.
"""

DISTRICTS = [
    {"district": "Kolkata", "state": "West Bengal", "latitude": 22.5726, "longitude": 88.3639},
    {"district": "Siliguri", "state": "West Bengal", "latitude": 26.7271, "longitude": 88.3953},
    {"district": "New Delhi", "state": "Delhi", "latitude": 28.6139, "longitude": 77.2090},
    {"district": "Mumbai City", "state": "Maharashtra", "latitude": 19.0760, "longitude": 72.8777},
    {"district": "Bengaluru Urban", "state": "Karnataka", "latitude": 12.9716, "longitude": 77.5946},
    {"district": "Chennai", "state": "Tamil Nadu", "latitude": 13.0827, "longitude": 80.2707},
    {"district": "Hyderabad", "state": "Telangana", "latitude": 17.3850, "longitude": 78.4867},
    {"district": "Ahmedabad", "state": "Gujarat", "latitude": 23.0225, "longitude": 72.5714},
    {"district": "Jaipur", "state": "Rajasthan", "latitude": 26.9124, "longitude": 75.7873},
    {"district": "Lucknow", "state": "Uttar Pradesh", "latitude": 26.8467, "longitude": 80.9462},
    {"district": "Patna", "state": "Bihar", "latitude": 25.5941, "longitude": 85.1376},
    {"district": "Bhopal", "state": "Madhya Pradesh", "latitude": 23.2599, "longitude": 77.4126},
]
