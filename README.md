# ML-Based Network Intrusion Detection System

A learning project to classify network-flow records as normal or attack
using the UNSW-NB15 dataset and classical machine learning.

Python used for initial setup: 3.12.4

## Dataset

This project uses the prepared training and testing subsets of UNSW-NB15.

Official source:
[UNSW-NB15 dataset](https://research.unsw.edu.au/projects/unsw-nb15-dataset)

Download date: 2026-09-12.

To obtain the data, follow the download link on the official page and
place these files in `data/raw/`:

| File | Purpose |
|---|---|
| `UNSW_NB15_training-set.csv` | Training/development data: 175,341 rows |
| `UNSW_NB15_testing-set.csv` | Reserved final test data: 82,332 rows |
| `NUSW-NB15_features.csv` | Feature descriptions; downloaded spelling preserved |

Both prepared data CSVs contain 45 columns, including identifiers and
target annotations.

Original files are preserved unchanged in `data/raw/` and excluded from Git.
Any derived datasets will be stored separately in `data/processed/`.

The official training set will supply training and validation data.
The official test set is reserved for evaluation after model and threshold
decisions are settled.

### Attribution

Nour Moustafa and Jill Slay, “UNSW-NB15: a comprehensive data set for
network intrusion detection systems (UNSW-NB15 network data set),”
MilCIS, 2015.

See the official dataset page for the complete citation requirements
and usage terms.

## Error analysis and limitations

On the official test set, the selected model produces 9,445 false
alarms and misses 785 attacks.

- Normal records with service "-" account for 7,968 false alarms,
  while HTTP accounts for another 1,164. Together, these categories
  contribute 96.7% of all false alarms.
- Normal FTP records have a 40.90% false-positive rate
  (310 of 758 records).
- Fuzzers account for 693 missed attacks, representing 88.3% of
  all missed attacks. Their category-specific miss rate is 11.43%.
- Results for very small groups require caution. For example,
  the 100% false-positive rate for RADIUS is based on two records.

These findings describe associations in this benchmark, not the
causes of individual predictions. Strong overall attack recall
does not imply equally strong performance across attack categories.

The model's 25.53% test false-positive rate is a substantial limitation.
Test-set error analysis was used for reporting, not to retune the model.