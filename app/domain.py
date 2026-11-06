"""Financial invariants and robust, explainable anomaly scoring."""
from statistics import median


def anomaly(amount: int, history: list[int]) -> dict:
    if len(history) < 5:
        return {'status': 'insufficient_history', 'score': None, 'samples': len(history)}
    center = median(history)
    mad = median(abs(x - center) for x in history)
    # A scale floor prevents an identical historical sample from dividing by zero.
    scale = max(1.4826 * mad, center * 0.05, 1)
    score = abs(amount - center) / scale
    return {'status': 'review' if score > 3.5 else 'normal', 'score': round(score, 4),
            'median_cents': center, 'scale_cents': round(scale, 2), 'samples': len(history),
            'model': 'median-mad-v1'}
