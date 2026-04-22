# eAudit capture — PIDSMaker metadata

**Source**: eAudit (`./eaudit -P`) on Ubuntu 22.04 / kernel 6.8

## Time range

- start: `2026-04-15T05:41:36.217000+00:00`  (`timestamp_rec=1776231696216999936`)
- end:   `2026-04-15T05:41:49.897000+00:00`  (`timestamp_rec=1776231709897000192`)
- span:  ~13.7 seconds

## Attack time window(s)

**No real attacks in this capture.** The following window and the rows in `ground_truth.csv` are RANDOM PLACEHOLDERS so downstream tooling can be exercised end-to-end. Replace before any evaluation.

- Attack-PLACEHOLDER: `2026-04-15T05:41:40.777000+00:00` to `2026-04-15T05:41:45.337000+00:00`
  (timestamp_rec range: `1776231700777000021` .. `1776231705337000106`)

## Day classification (benign vs. attack)

- 2026-04-15: ATTACK (placeholder)

## Operation types present

Total distinct operations: **8**

| operation | count |
|---|---:|
| `EVENT_READ` | 2368 |
| `EVENT_CLOSE` | 2045 |
| `EVENT_OPEN` | 2017 |
| `EVENT_RECVFROM` | 223 |
| `EVENT_SENDTO` | 220 |
| `EVENT_CONNECT` | 36 |
| `EVENT_EXECUTE` | 26 |
| `EVENT_WRITE` | 8 |

## Node / event counts

- netflow_node_table: 13
- subject_node_table: 45
- file_node_table:    1502
- event_table:        6943
- ground_truth.csv:   15 (placeholder)
