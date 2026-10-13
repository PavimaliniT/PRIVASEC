import numpy as np
import pandas as pd
from typing import Tuple


def generate_synthetic_security_dataset(
    n_benign: int = 2000,
    n_anomalous: int = 150,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Generates synthetic security feature dataset with benign and attack scenarios:
    Features:
    0: requests_per_minute
    1: failed_logins_5m
    2: time_of_day_deviation (0.0=peak work hour, 1.0=middle of night)
    3: device_novelty (0=known, 1=new)
    4: endpoint_rarity (0=common like /dashboard, 1=rare admin/export)
    5: export_volume_kb
    6: access_denial_frequency
    """
    rng = np.random.default_rng(random_state)

    # 1. Benign Normal Behavior
    # Normal users: ~5-35 req/min, 0 failed logins, normal hours (dev 0.0 - 0.25), known device (95%), low export (0-50KB)
    benign_req_rate = rng.normal(loc=18.0, scale=8.0, size=n_benign).clip(1, 55)
    benign_failed_logins = rng.choice([0, 1], size=n_benign, p=[0.97, 0.03])
    benign_hour_dev = rng.beta(a=1.5, b=6.0, size=n_benign).clip(0.0, 0.45)
    benign_device_novelty = rng.choice([0.0, 1.0], size=n_benign, p=[0.94, 0.06])
    benign_endpoint_rarity = rng.beta(a=1.2, b=4.0, size=n_benign).clip(0.0, 0.5)
    benign_export_kb = rng.exponential(scale=25.0, size=n_benign).clip(0, 200)
    benign_denials = rng.choice([0, 1], size=n_benign, p=[0.98, 0.02])

    benign_df = pd.DataFrame({
        "requests_per_minute": benign_req_rate,
        "failed_logins_5m": benign_failed_logins,
        "time_of_day_deviation": benign_hour_dev,
        "device_novelty": benign_device_novelty,
        "endpoint_rarity": benign_endpoint_rarity,
        "export_volume_kb": benign_export_kb,
        "access_denial_frequency": benign_denials,
        "label": 0  # 0 = Benign
    })

    # 2. Attack / Anomalous Scenarios:
    # A: Credential Stuffing / Brute Force (High failed logins, high req/min, new device)
    n_bf = n_anomalous // 3
    bf_df = pd.DataFrame({
        "requests_per_minute": rng.uniform(40, 120, size=n_bf),
        "failed_logins_5m": rng.integers(5, 25, size=n_bf),
        "time_of_day_deviation": rng.uniform(0.3, 0.9, size=n_bf),
        "device_novelty": np.ones(n_bf),
        "endpoint_rarity": rng.uniform(0.2, 0.6, size=n_bf),
        "export_volume_kb": rng.uniform(0, 10, size=n_bf),
        "access_denial_frequency": rng.integers(4, 15, size=n_bf),
        "label": 1
    })

    # B: Data Exfiltration / Unusual Bulk Export (Huge export volume, rare endpoints, off hours)
    n_exfil = n_anomalous // 3
    exfil_df = pd.DataFrame({
        "requests_per_minute": rng.uniform(25, 70, size=n_exfil),
        "failed_logins_5m": np.zeros(n_exfil),
        "time_of_day_deviation": rng.uniform(0.6, 0.95, size=n_exfil),
        "device_novelty": rng.choice([0.0, 1.0], size=n_exfil, p=[0.4, 0.6]),
        "endpoint_rarity": rng.uniform(0.7, 0.99, size=n_exfil),
        "export_volume_kb": rng.uniform(2500, 50000, size=n_exfil),
        "access_denial_frequency": rng.integers(0, 3, size=n_exfil),
        "label": 1
    })

    # C: API Burst / Scrape Attack (Extreme req/min, high endpoint exploration)
    n_burst = n_anomalous - n_bf - n_exfil
    burst_df = pd.DataFrame({
        "requests_per_minute": rng.uniform(150, 450, size=n_burst),
        "failed_logins_5m": rng.integers(0, 3, size=n_burst),
        "time_of_day_deviation": rng.uniform(0.2, 0.8, size=n_burst),
        "device_novelty": np.ones(n_burst),
        "endpoint_rarity": rng.uniform(0.6, 0.95, size=n_burst),
        "export_volume_kb": rng.uniform(50, 800, size=n_burst),
        "access_denial_frequency": rng.integers(5, 20, size=n_burst),
        "label": 1
    })

    full_df = pd.concat([benign_df, bf_df, exfil_df, burst_df], ignore_index=True)
    full_df = full_df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)

    X = full_df.drop(columns=["label"])
    y = full_df["label"]
    return X, y
