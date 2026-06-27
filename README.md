# AI-ML in Healthcare

This repository contains a project for generating and evaluating dirty Entity Resolution datasets in the medical domain.

The basic workflow is:

1. Generate synthetic patient records with Synthea.
2. Use the generated patient table as a clean base dataset.
3. Introduce artificial duplicates, typographical errors, missing values, and spelling variations.
4. Evaluate Entity Resolution / filtering methods with PyJedAI.

Real patient data are difficult to obtain because of privacy restrictions. Therefore, this project starts from synthetic medical data and then intentionally introduces artificial noise for Entity Resolution experiments.

## Environment setup

Create the Conda environment:

```bash
conda env create -f environment.yml
conda activate aiml-healthcare
```

If the environment already exists:

```bash
conda activate aiml-healthcare
```

Check the installation:

```bash
python - <<'PY'
import pandas as pd
import numpy as np
import recordlinkage
import pyjedai

print("pandas:", pd.__version__)
print("numpy:", np.__version__)
print("recordlinkage:", recordlinkage.__version__)
print("pyjedai: import ok")
PY

java -version
```

## Clean Synthea base dataset

The clean base dataset is generated with Synthea. Synthea itself and the full raw export are not committed because the raw output can become large.

The repository contains:

```text
scripts/generate_synthea_sample.sh
data/sample/synthea_seed42_100/patients.csv
data/sample/synthea_seed42_100/metadata.txt
```

To regenerate the dataset:

```bash
conda activate aiml-healthcare
./scripts/generate_synthea_sample.sh
```

The script uses:

```text
Synthea commit: d02dcd65b0c8cd96d91ae7660f3570daf0fb41a1
Seed: 42
Clinician seed: 4242
Population parameter: 100
Reference date: 20260627
Location: Massachusetts
CSV export: enabled
FHIR export: disabled
```

The full raw Synthea export is written to:

```text
data/raw/synthea_seed42_100/
```

This folder is ignored by Git.

The committed clean base table is:

```text
data/sample/synthea_seed42_100/patients.csv
```

This `patients.csv` file is the clean base table for the first Dirty Entity Resolution experiments. The file is reproducible with the script above. The current committed sample has 107 rows and 28 columns. Although the population parameter is 100, Synthea can create additional records for deceased patients.

## Dirty Entity Resolution sample dataset

The clean Synthea base table is used to generate a small dirty Entity Resolution dataset.

The dirty dataset is generated with:

```bash
python scripts/create_dirty_er_dataset.py
```

The script reads:

```text
data/sample/synthea_seed42_100/patients.csv
```

and writes:

```text
data/sample/dirty_er_seed42_100/patients_dirty.csv
data/sample/dirty_er_seed42_100/ground_truth.csv
data/sample/dirty_er_seed42_100/record_entity_mapping.csv
data/sample/dirty_er_seed42_100/metadata.txt
```

The default parameters are:

```text
Seed: 42
Duplicate rate: 0.30
Typo rate: 0.20
Missing value rate: 0.10
Date error rate: 0.05
ZIP error rate: 0.10
```

For the current small sample, this creates:

```text
Clean records: 107
Artificial duplicates: 32
Total dirty records: 139
Ground-truth duplicate pairs: 32
```

The dirty dataset contains Febrl-inspired artificial errors:

* character deletion
* character insertion
* character substitution
* adjacent character transposition
* missing values
* small date shifts
* ZIP code digit changes

Direct identifiers such as the original Synthea `Id`, `SSN`, driver license number, and passport number are excluded from `patients_dirty.csv`, because these fields would make the Entity Resolution task unrealistically easy.

The `ground_truth.csv` file contains the true duplicate record pairs and can later be used to evaluate recall, precision, and filtering/blocking quality.

The `record_entity_mapping.csv` file is included as an additional debug and evaluation aid. It maps each visible `record_id` to an internal `entity_id`, but this file should not be used as input for matching methods.

To verify that the generated dirty dataset is reproducible, run the script twice and compare the output files:

```bash
cp data/sample/dirty_er_seed42_100/patients_dirty.csv /tmp/patients_dirty_run1.csv
cp data/sample/dirty_er_seed42_100/ground_truth.csv /tmp/ground_truth_run1.csv

python scripts/create_dirty_er_dataset.py

cmp -s /tmp/patients_dirty_run1.csv data/sample/dirty_er_seed42_100/patients_dirty.csv \
  && echo "patients_dirty.csv is reproducible" \
  || echo "patients_dirty.csv differs"

cmp -s /tmp/ground_truth_run1.csv data/sample/dirty_er_seed42_100/ground_truth.csv \
  && echo "ground_truth.csv is reproducible" \
  || echo "ground_truth.csv differs"
```

The next project step is to run a small PyJedAI smoke test on `patients_dirty.csv` and evaluate whether the generated `ground_truth.csv` can be used correctly for Dirty ER evaluation.

