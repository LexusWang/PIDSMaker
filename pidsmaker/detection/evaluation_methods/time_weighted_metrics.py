"""Time-weighted precision, recall, and F1 metrics at node level.

Nodes that appear earlier (lower timestamp) receive higher weight, so that
early-detected attack nodes contribute more to the final score.
"""

import warnings

import numpy as np


def normalize_timestamps(timestamps):
    """Normalize timestamps to tau in [0, 1].

    Args:
        timestamps: list or numpy array of raw timestamps (one per node).

    Returns:
        numpy array of tau values in [0, 1]. Returns zeros if all timestamps
        are identical (degenerate case; weights become uniform).
    """
    ts = np.asarray(timestamps, dtype=float)
    ts_min = ts.min()
    ts_max = ts.max()
    if ts_max == ts_min:
        return np.zeros_like(ts)
    return (ts - ts_min) / (ts_max - ts_min)


def linear_weight(tau):
    """Compute linear time weights: w = 1 - tau.

    Earlier nodes (tau close to 0) receive weight close to 1;
    later nodes (tau close to 1) receive weight close to 0.

    Args:
        tau: numpy array of normalized timestamps in [0, 1].

    Returns:
        numpy array of weights.
    """
    return 1.0 - tau


def exponential_weight(tau, lambda_param):
    """Compute exponential time weights: w = exp(-lambda * tau).

    Args:
        tau: numpy array of normalized timestamps in [0, 1].
        lambda_param: float, decay rate (>= 0).

    Returns:
        numpy array of weights.
    """
    return np.exp(-lambda_param * tau)


def time_weighted_precision(y_true, y_pred, weights):
    """Compute time-weighted precision.

    weighted_TP / weighted_predicted_positive

    Args:
        y_true: array-like of ground-truth binary labels.
        y_pred: array-like of predicted binary labels.
        weights: array-like of per-node weights.

    Returns:
        float: time-weighted precision, or 0.0 if no positive predictions.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    weights = np.asarray(weights, dtype=float)

    tp_mask = (y_true == 1) & (y_pred == 1)
    pp_mask = y_pred == 1

    weighted_tp = np.sum(weights[tp_mask])
    weighted_pp = np.sum(weights[pp_mask])

    if weighted_pp == 0.0:
        warnings.warn(
            "time_weighted_precision: denominator (weighted predicted positives) is 0. "
            "Returning 0.0.",
            RuntimeWarning,
            stacklevel=2,
        )
        return 0.0
    return weighted_tp / weighted_pp


def time_weighted_recall(y_true, y_pred, weights):
    """Compute time-weighted recall.

    weighted_TP / weighted_actual_positive

    Args:
        y_true: array-like of ground-truth binary labels.
        y_pred: array-like of predicted binary labels.
        weights: array-like of per-node weights.

    Returns:
        float: time-weighted recall, or 0.0 if no actual positives.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    weights = np.asarray(weights, dtype=float)

    tp_mask = (y_true == 1) & (y_pred == 1)
    ap_mask = y_true == 1

    weighted_tp = np.sum(weights[tp_mask])
    weighted_ap = np.sum(weights[ap_mask])

    if weighted_ap == 0.0:
        warnings.warn(
            "time_weighted_recall: denominator (weighted actual positives) is 0. "
            "Returning 0.0.",
            RuntimeWarning,
            stacklevel=2,
        )
        return 0.0
    return weighted_tp / weighted_ap


def time_weighted_f1(precision, recall):
    """Compute harmonic mean of time-weighted precision and recall.

    Args:
        precision: float, time-weighted precision.
        recall: float, time-weighted recall.

    Returns:
        float: time-weighted F1, or 0.0 if both precision and recall are 0.
    """
    if precision + recall == 0.0:
        return 0.0
    return 2.0 * precision * recall / (precision + recall)


def compute_time_weighted_metrics(
    y_true,
    y_pred,
    timestamps,
    scheme="linear",
    lambda_param=1.0,
):
    """Compute time-weighted precision, recall, and F1 at node level.

    Args:
        y_true: list or numpy array of ground-truth binary labels (one per node).
        y_pred: list or numpy array of predicted binary labels (one per node).
        timestamps: list or numpy array of raw first-appearance timestamps
            (one per node).
        scheme: str, weighting scheme — 'linear' or 'exponential'.
        lambda_param: float, decay rate for exponential scheme (ignored for linear).

    Returns:
        dict with keys:
            tw_precision (float), tw_recall (float), tw_f1 (float),
            tw_scheme (str).
    """
    _zero = {"tw_precision": 0.0, "tw_recall": 0.0, "tw_f1": 0.0, "tw_scheme": scheme}

    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    timestamps = np.asarray(timestamps, dtype=float)

    if y_true.size == 0:
        return _zero

    tau = normalize_timestamps(timestamps)

    if scheme == "linear":
        weights = linear_weight(tau)
    elif scheme == "exponential":
        weights = exponential_weight(tau, lambda_param)
    else:
        raise ValueError(f"Unknown time-weighting scheme: {scheme!r}. Use 'linear' or 'exponential'.")

    precision = time_weighted_precision(y_true, y_pred, weights)
    recall = time_weighted_recall(y_true, y_pred, weights)
    f1 = time_weighted_f1(precision, recall)

    return {
        "tw_precision": round(float(precision), 5),
        "tw_recall": round(float(recall), 5),
        "tw_f1": round(float(f1), 5),
        "tw_scheme": scheme,
    }
