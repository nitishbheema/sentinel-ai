# SentinelAI Machine Learning Threat Detection & Evaluation Report

## 1. Executive Summary

SentinelAI implements a machine-learning pipeline for cyber threat detection combining:
1. **Supervised Classification (Random Forest)**: Multi-class attack categorizer trained on flow telemetry adhering to the Canadian Institute for Cybersecurity CICIDS2017 schema.
2. **Unsupervised Anomaly Detection (Isolation Forest)**: Zero-day and anomalous deviation detector trained strictly on verified benign traffic.

Both models were trained and evaluated following rigorous ML engineering standards:
- **No Data Leakage**: Feature scalers (`StandardScaler`) and categorical encoders were fitted strictly on training data splits and applied downstream to the test set and live inference.
- **Realistic Benchmarking**: Evaluated on an explicitly labelled test set of 2,400 independent flows (following 9,600 training flows).
- **Zero Fabrication**: All reported metrics represent actual model evaluations recorded in `ml-engine/models/evaluation_metrics.json`.

---

## 2. Dataset & Feature Engineering

### 2.1 Feature Definitions (CICIDS2017 Schema)
The pipeline extracts 19 statistical flow attributes capturing directional packet sizing, inter-arrival times (IAT), and TCP protocol flags:

| Feature Name | Type | Description |
| :--- | :--- | :--- |
| `destination_port` | Integer | Destination transport layer port |
| `flow_duration` | Float | Microseconds flow remained active |
| `tot_fwd_pkts` | Integer | Total packets transmitted in forward direction |
| `tot_bwd_pkts` | Integer | Total packets transmitted in backward direction |
| `tot_len_fwd_pkts` | Float | Total payload bytes in forward direction |
| `tot_len_bwd_pkts` | Float | Total payload bytes in backward direction |
| `flow_byts_s` | Float | Flow transfer throughput (Bytes / second) |
| `flow_pkts_s` | Float | Flow packet rate (Packets / second) |
| `flow_iat_mean` | Float | Mean inter-arrival time between packets |
| `fwd_pkt_len_max` | Float | Maximum packet length in forward direction |
| `fwd_pkt_len_min` | Float | Minimum packet length in forward direction |
| `fwd_pkt_len_mean` | Float | Mean packet length in forward direction |
| `fwd_pkt_len_std` | Float | Standard deviation of forward packet lengths |
| `fwd_iat_tot` | Float | Total forward inter-arrival time |
| `bwd_iat_tot` | Float | Total backward inter-arrival time |
| `psh_flag_cnt` | Integer | Number of packets with PSH flag set |
| `ack_flag_cnt` | Integer | Number of packets with ACK flag set |
| `syn_flag_cnt` | Integer | Number of packets with SYN flag set |
| `rst_flag_cnt` | Integer | Number of packets with RST flag set |

### 2.2 Dataset Partitioning
- **Training Set**: 9,600 flows (80%)
- **Test Set**: 2,400 flows (20%)
- **Class Labels**: `BENIGN`, `Botnet`, `BruteForce`, `DDoS`, `PortScan`, `WebAttack`.

---

## 3. Supervised Model: Random Forest Classifier

### 3.1 Model Architecture & Hyperparameters
- **Estimators**: 100 decision trees
- **Max Depth**: 15
- **Criterion**: Gini Impurity
- **Class Weighting**: Balanced to prevent majority class bias towards benign traffic.
- **Random State**: 42 for complete reproducibility.

### 3.2 Evaluation Metrics
- **Overall Accuracy**: **97.25%**
- **Weighted Precision**: **96.99%**
- **Weighted Recall**: **97.25%**
- **Weighted F1-Score**: **0.9700**
- **False Positive Rate (FPR)**: **0.0000** (0 false positives on benign validation traffic)

### 3.3 Confusion Matrix
Evaluating 2,400 test flows across all 6 attack categories:

```
                  Predicted
             BENIGN  Botnet  BruteForce  DDoS  PortScan  WebAttack
BENIGN         1577       0           0     0         0          0
Botnet            0      17           0     0         0         47
BruteForce        0       0         167     0         0          0
DDoS              0       0           0   234         0          0
PortScan          0       0           0     0       233          0
WebAttack         0      19           0     0         0        106
```

### 3.4 Feature Importance Ranking
The top 10 features driving Random Forest classifications:

1. **`fwd_pkt_len_max`** (20.95%): Extreme packet sizes distinguish data exfiltration and buffer exploits.
2. **`fwd_pkt_len_min`** (12.91%): Minimum packet sizes differentiate small probe handshakes from normal HTTP payloads.
3. **`tot_len_bwd_pkts`** (12.21%): Response volume indicates server data transfer vs probe termination.
4. **`fwd_pkt_len_std`** (8.25%): High variance in packet sizes correlates with varied web application traffic.
5. **`fwd_pkt_len_mean`** (7.10%): Average forward payload density.
6. **`tot_bwd_pkts`** (6.40%): Total response packet count.
7. **`bwd_iat_tot`** (5.91%): Response latency and server processing time.
8. **`ack_flag_cnt`** (5.18%): TCP session completion markers.
9. **`tot_len_fwd_pkts`** (4.81%): Outbound data transfer volume.
10. **`tot_fwd_pkts`** (3.33%): Number of client-initiated packets.

---

## 4. Unsupervised Model: Isolation Forest Anomaly Detection

### 4.1 Methodology
Isolation Forest detects outliers by randomly selecting features and split values. Anomalous network flows require fewer tree partitions to isolate than normal baseline flows.

- **Training Baseline**: Trained exclusively on 6,307 confirmed benign network flows.
- **Contamination Rate**: $0.08$ (assumed expected ambient anomaly rate).
- **Number of Estimators**: 100 trees.

### 4.2 Anomaly Score Calculation
Isolation Forest produces decision function outputs where negative scores indicate outliers. SentinelAI normalizes this score to a continuous range from $0.0$ to $1.0$:

$$\text{Anomaly Score} = \min(1.0, \max(0.0, -2.0 \times \text{decision\_function}))$$

When $\text{Anomaly Score} > 0.65$, the flow is flagged as anomalous and forwarded to the correlation and risk engine.

---

## 5. Model Explainability & Artifact Persistence

All trained models and metadata are serialized under `ml-engine/models/`:
- `random_forest.joblib`: Persisted Scikit-learn Random Forest model.
- `isolation_forest.joblib`: Persisted Scikit-learn Isolation Forest model.
- `scaler.joblib`: Fitted `StandardScaler` transforming features into standard normal distributions.
- `label_encoder.joblib`: Encoded integer mappings for attack classes.
- `evaluation_metrics.json`: Complete statistical evaluation report.

During live inference (`POST /api/v1/ml/predict`), SentinelAI dynamically computes local feature contributions, providing SOC analysts with clear explanations for every detected anomaly.
