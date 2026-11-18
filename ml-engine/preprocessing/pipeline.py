import numpy as np
import pandas as pd
from typing import List, Tuple
from sklearn.preprocessing import StandardScaler


FEATURE_COLUMNS = [
    "destination_port",
    "flow_duration",
    "tot_fwd_pkts",
    "tot_bwd_pkts",
    "tot_len_fwd_pkts",
    "tot_len_bwd_pkts",
    "fwd_pkt_len_max",
    "fwd_pkt_len_min",
    "fwd_pkt_len_mean",
    "fwd_pkt_len_std",
    "flow_byts_s",
    "flow_pkts_s",
    "flow_iat_mean",
    "fwd_iat_tot",
    "bwd_iat_tot",
    "syn_flag_cnt",
    "rst_flag_cnt",
    "psh_flag_cnt",
    "ack_flag_cnt"
]


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans infinite and NaN values often present in network flow datasets
    """
    df = df.copy()
    # Replace inf with nan
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    # Fill nan with median
    for col in FEATURE_COLUMNS:
        if col in df.columns:
            median_val = df[col].median()
            df[col].fillna(0.0 if np.isnan(median_val) else median_val, inplace=True)
    return df


def extract_features_from_event(event_dict: dict) -> np.ndarray:
    """
    Extracts numerical feature vector for real-time inference
    """
    features = []
    norm = event_dict.get("normalized_data") or {}
    raw = event_dict.get("raw_data") or {}

    dst_port = event_dict.get("destination_port") or norm.get("destination_port") or raw.get("id_resp_p") or 80
    features.append(float(dst_port))

    duration = norm.get("duration") or raw.get("duration") or 0.5
    features.append(float(duration))

    fwd_pkts = raw.get("fwd_pkts") or norm.get("orig_pkts") or 5
    features.append(float(fwd_pkts))

    bwd_pkts = raw.get("bwd_pkts") or norm.get("resp_pkts") or 4
    features.append(float(bwd_pkts))

    orig_bytes = norm.get("orig_bytes") or raw.get("orig_bytes") or 500
    features.append(float(orig_bytes))

    resp_bytes = norm.get("resp_bytes") or raw.get("resp_bytes") or 1200
    features.append(float(resp_bytes))

    fwd_len_max = raw.get("fwd_pkt_len_max") or 1500.0
    features.append(float(fwd_len_max))

    fwd_len_min = raw.get("fwd_pkt_len_min") or 40.0
    features.append(float(fwd_len_min))

    fwd_len_mean = raw.get("fwd_pkt_len_mean") or 450.0
    features.append(float(fwd_len_mean))

    fwd_len_std = raw.get("fwd_pkt_len_std") or 50.0
    features.append(float(fwd_len_std))

    # Flow rates
    dur = max(float(duration), 0.001)
    features.append(float((orig_bytes + resp_bytes) / dur))
    features.append(float((fwd_pkts + bwd_pkts) / dur))

    features.append(float(dur / max(fwd_pkts + bwd_pkts, 1)))  # flow_iat_mean
    features.append(float(dur * 0.6))  # fwd_iat_tot
    features.append(float(dur * 0.4))  # bwd_iat_tot

    # Flags
    features.append(float(raw.get("syn_flag_cnt", 1)))
    features.append(float(raw.get("rst_flag_cnt", 0)))
    features.append(float(raw.get("psh_flag_cnt", 1)))
    features.append(float(raw.get("ack_flag_cnt", 1)))

    return np.array([features], dtype=np.float32)
