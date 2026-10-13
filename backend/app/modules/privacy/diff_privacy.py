import numpy as np
from typing import List, Dict, Any


def add_laplace_noise(val: float, sensitivity: float, epsilon: float) -> float:
    """
    Applies the classical Laplace mechanism:
    Noise ~ Laplace(0, scale = sensitivity / epsilon).
    """
    if epsilon <= 0:
        raise ValueError("Epsilon must be greater than 0")
    scale = sensitivity / epsilon
    noise = float(np.random.laplace(0, scale))
    return val + noise


def compute_dp_count(actual_count: int, epsilon: float = 1.0) -> Dict[str, Any]:
    """
    Differential private count query.
    Global sensitivity for a counting query is 1 (addition/removal of one record alters count by at most 1).
    """
    sensitivity = 1.0
    scale = sensitivity / epsilon
    noise = float(np.random.laplace(0, scale))
    noisy_count = max(0, int(round(actual_count + noise)))
    
    # 95% Laplace interval: +/- scale * ln(1 / 0.05) ~= scale * 2.9957
    margin_95 = round(scale * np.log(1.0 / 0.05), 2)

    return {
        "mechanism": "Laplace Mechanism",
        "query_type": "COUNT",
        "epsilon": epsilon,
        "sensitivity": sensitivity,
        "laplace_scale": round(scale, 4),
        "actual_value": actual_count,
        "noisy_value": noisy_count,
        "noise_added": round(noisy_count - actual_count, 2),
        "confidence_interval_95_pct": f"+/- {margin_95}",
        "privacy_guarantee": f"e^({epsilon}) = {round(np.exp(epsilon), 3)}-differential privacy"
    }


def compute_dp_average(values: List[float], min_val: float, max_val: float, epsilon: float = 1.0) -> Dict[str, Any]:
    """
    Differential private mean query for bounded numerical domain [min_val, max_val].
    Sensitivity = (max_val - min_val) / n
    """
    if not values:
        return {"error": "Empty dataset"}
    
    n = len(values)
    # Clip values to bounds
    clipped = [max(min_val, min(max_val, v)) for v in values]
    actual_mean = float(np.mean(clipped))
    
    sensitivity = (max_val - min_val) / n
    scale = sensitivity / epsilon
    noise = float(np.random.laplace(0, scale))
    noisy_mean = round(actual_mean + noise, 3)

    return {
        "mechanism": "Laplace Mechanism",
        "query_type": "MEAN",
        "sample_size": n,
        "domain_bounds": [min_val, max_val],
        "epsilon": epsilon,
        "sensitivity": round(sensitivity, 4),
        "laplace_scale": round(scale, 4),
        "actual_value": round(actual_mean, 3),
        "noisy_value": noisy_mean,
        "noise_added": round(noisy_mean - actual_mean, 3),
        "privacy_guarantee": f"e^({epsilon}) = {round(np.exp(epsilon), 3)}-differential privacy"
    }
