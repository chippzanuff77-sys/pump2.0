from math import sqrt


FEATURE_KEYS = [
    "ret_5d",
    "ret_10d",
    "ret_20d",
    "rv_ratio",
    "atr_pct",
    "range_compression_score",
    "breakout_distance",
    "rsi_14",
    "sma20_distance",
    "sma50_distance",
]


def euclidean_similarity(current: dict[str, float], historical: dict[str, float]) -> float:
    total = 0.0
    for key in FEATURE_KEYS:
        total += (current.get(key, 0.0) - historical.get(key, 0.0)) ** 2
    distance = sqrt(total)
    return 1.0 / (1.0 + distance)


def rule_based_score(features: dict[str, float]) -> float:
    score = 0.0
    if features.get("rv_ratio", 0.0) > 2.0:
        score += 3.0
    if features.get("breakout_distance", -999.0) > -1.0:
        score += 2.0
    if 0.0 < features.get("range_compression_score", 0.0) < 1.0:
        score += 1.5
    if features.get("sma20_distance", 0.0) > 0.0:
        score += 1.0
    if features.get("ret_30d", 0.0) > -10.0:
        score += 1.0
    if features.get("avg_dollar_volume_20d", 0.0) > 500_000:
        score += 1.5
    return score

