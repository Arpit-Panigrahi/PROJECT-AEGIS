import numpy as np

def shannon_entropy(buf: bytes) -> float:
    if not buf:
        return 0.0
    counts = np.bincount(np.frombuffer(buf, dtype=np.uint8), minlength=256)
    n = len(buf)
    probs = counts[counts > 0] / n
    return float(-(probs * np.log2(probs)).sum())

def miller_madow(buf: bytes) -> float:
    counts = np.bincount(np.frombuffer(buf, dtype=np.uint8), minlength=256)
    n = len(buf)
    k_obs = int((counts > 0).sum())
    h = shannon_entropy(buf)
    bias_correction = (k_obs - 1) / (2 * n * np.log(2))
    return h + bias_correction
