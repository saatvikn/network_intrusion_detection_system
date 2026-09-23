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

The official training set was divided into 140,272 training records and
35,069 validation records. Identical input patterns were kept together
to prevent them from appearing in both partitions.

The official test set was evaluated after selecting the model and
decision threshold.

### Attribution

Nour Moustafa and Jill Slay, “UNSW-NB15: a comprehensive data set for
network intrusion detection systems (UNSW-NB15 network data set),”
MilCIS, 2015.

See the official dataset page for the complete citation requirements
and usage terms.

## Features

- Classifies recorded network flows as normal or attack.
- Provides single-record prediction through a FastAPI endpoint.
- Includes a Next.js dashboard with six sample flows.
- Supports CSV batch prediction with per-record results and summary counts.
- Runs locally; no cloud services are required.

This is a benchmark demonstration, not a live packet-capture or
firewall-blocking system.

## Methodology

The project compares a majority-class dummy baseline, logistic regression,
a decision tree, a random forest, and XGBoost.

Input records contain 41 features:
- 38 numerical features.
- Three categorical features: protocol, service, and connection state.

The identifier and target columns are excluded from model inputs.
`is_ftp_login` is also excluded because it duplicates `ct_ftp_cmd`
in the development data.

Categorical features are one-hot encoded. Preprocessing is fitted on
training data and saved together with the classifier in one pipeline.

A grouped training/validation split keeps identical input patterns
together. Hyperparameter tuning uses three-fold grouped cross-validation
within the training partition.

## Model comparison

Results below are from the validation partition at a threshold of 0.5.
Precision and recall refer to the attack class.

| Model | Accuracy | Precision | Recall | False-positive rate |
|---|---:|---:|---:|---:|
| Dummy | 68.06% | 68.06% | 100.00% | 100.00% |
| Logistic regression | 93.68% | 92.44% | 98.80% | 17.22% |
| Decision tree | 94.39% | 94.77% | 97.11% | 11.42% |
| Random forest | 93.59% | 91.41% | 99.98% | 20.03% |
| XGBoost | 95.20% | 95.62% | 97.40% | 9.51% |
| Tuned XGBoost | 95.66% | 96.11% | 97.58% | 8.42% |

Tuned XGBoost was selected based on its validation results, including
an F1 score of 96.84%.

Selected settings:
- 200 trees.
- Maximum depth: 6.
- Learning rate: 0.1.
- Decision threshold: 0.5.

The threshold achieved the highest validation F1 among the thresholds
examined. It is not claimed to be optimal for a real network's operating
costs.

## Official test results

The selected pipeline was evaluated on 82,332 official test records.
The model remained fitted on the 140,272-record training partition.

| Metric | Result |
|---|---:|
| Accuracy | 87.57% |
| Attack precision | 82.51% |
| Attack recall | 98.27% |
| Attack F1 | 89.70% |
| False-positive rate | 25.53% |
| ROC AUC | 0.9838 |
| Average precision | 0.9882 |

| Actual class | Predicted normal | Predicted attack |
|---|---:|---:|
| Normal | 27,555 | 9,445 |
| Attack | 785 | 44,547 |

These test results, rather than the higher validation results, describe
the final held-out evaluation.

Full-precision metrics and error-analysis tables are saved in
`reports/metrics/`.

## Architecture

Next.js dashboard → FastAPI → saved preprocessing and XGBoost pipeline

The backend loads the saved pipeline once per server process.
The frontend sends feature records and displays the returned predictions.
Training is performed separately from inference.

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

## Local setup

These commands target Windows PowerShell.

Prerequisites:
- Python 3.12; development used Python 3.12.4.
- Node.js 20.9 or newer, with npm.
- Git.
- The dataset files described above.

### Install dependencies

```powershell
git clone https://github.com/saatvikn/network_intrusion_detection_system.git
cd network_intrusion_detection_system

py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

npm --prefix frontend ci
```

### Prepare the split and train

Place the downloaded dataset files in `data/raw/`, then run:

```powershell
.\.venv\Scripts\python.exe -m src.prepare_split
.\.venv\Scripts\python.exe -m src.train
.\.venv\Scripts\python.exe -m src.prepare_samples
```

The split script recreates the notebook's training/validation assignments.
If a split file already exists, it verifies that the assignments match.

The training script uses the selected model settings and creates or
replaces `models/intrusion_detector.joblib`. It does not repeat the
hyperparameter search.

The samples script generates the JSON examples and demonstration CSV.

Raw datasets, processed splits, and trained model artifacts are excluded
from Git. The scripts recreate the derived files locally.

### Start the API

From the project root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.api:app --reload
```

API documentation: http://127.0.0.1:8000/docs

### Start the frontend

Create `frontend/.env.local` containing:

```dotenv
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

In a second terminal, from the project root:

```powershell
npm --prefix frontend run dev
```

Open http://localhost:3000.

Keep both terminals running. Restart the frontend after changing its
environment configuration.

### Run automated checks

The backend tests require the trained model artifact.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
npm --prefix frontend run lint
npm --prefix frontend run build
```

### Predict from the command line

```powershell
.\.venv\Scripts\python.exe -m src.predict tests/fixtures/example_record.json
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check that the service is running |
| GET | `/samples` | Retrieve demonstration flows |
| POST | `/predict` | Predict one JSON feature record |
| POST | `/predict-batch` | Upload a CSV for batch prediction |

The single-record endpoint accepts a JSON object containing a `record`
field. That field must contain exactly the 41 model inputs.

The batch endpoint accepts a multipart upload named `file`.

## CSV format

Use `data/demo_flows.csv` as a working example.

- UTF-8 encoding with a header row.
- Exactly the 41 input-feature columns; column order may vary.
- Exclude `id`, `label`, `attack_cat`, and `is_ftp_login`.
- Numerical values must be finite.
- Categorical values must be nonempty strings.
- Maximum 1,000 records and 2 MiB per file.

Invalid records cause the batch to be rejected with an error message.
Result row numbers start at 1 and exclude the header.

Summary counts describe predicted classes, not verified attack counts.

## Project structure

- `notebooks/`: data exploration, model experiments, and evaluation.
- `src/`: split preparation, training, prediction, and API code.
- `tests/`: prediction and API tests.
- `frontend/`: Next.js dashboard.
- `reports/metrics/`: saved evaluation results and error analysis.
- `data/`: local datasets and demonstration inputs.
- `models/`: locally generated model artifacts.