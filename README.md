# AI-ML in Healthcare

This repository contains a small reproducible setup for creating dirty Entity Resolution datasets in the medical domain.

The workflow is:

1. Generate synthetic patient data with Synthea.
2. Use the patient table as a clean base dataset.
3. Create artificial duplicates and add controlled noise.
4. Use the resulting dataset for Entity Resolution experiments, e.g. with PyJedAI.

The data are synthetic because real medical records are difficult to use due to privacy constraints.

## Setup

Create and activate the Conda environment:

```bash
conda env create -f environment.yml
conda activate aiml-healthcare
```

For later sessions, only activation is needed:

```bash
conda activate aiml-healthcare
```

## Clean Synthea dataset

The clean base table is generated with Synthea:

```bash
./scripts/generate_synthea_sample.sh
```

This creates the full raw Synthea export locally under:

```text
data/raw/synthea_seed42_100/
```

The raw export is ignored by Git. The committed clean sample is:

```text
data/sample/synthea_seed42_100/patients.csv
```

Generation parameters:

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

The committed clean sample contains 107 rows and 28 columns. Although the population parameter is 100, Synthea can include additional deceased patients.

## Dirty ER dataset

The dirty dataset is generated from the clean Synthea patient table:

```bash
python scripts/create_dirty_er_dataset.py
```

Output files:

```text
data/sample/dirty_er_seed42_100/patients_dirty.csv
data/sample/dirty_er_seed42_100/ground_truth.csv
data/sample/dirty_er_seed42_100/record_entity_mapping.csv
data/sample/dirty_er_seed42_100/metadata.txt
```

Default parameters:

```text
Seed: 42
Duplicate rate: 0.30
Typo rate: 0.20
Missing value rate: 0.10
Date error rate: 0.05
ZIP error rate: 0.10
```

For the current sample, this results in:

```text
Clean records: 107
Artificial duplicates: 32
Total dirty records: 139
Ground-truth duplicate pairs: 32
```

The dirty dataset contains Febrl-inspired artificial errors such as character edits, missing values, small date shifts, and ZIP code changes.

Direct identifiers such as Synthea `Id`, `SSN`, driver license number, and passport number are excluded from `patients_dirty.csv`, because they would make the matching task unrealistically easy.

`ground_truth.csv` contains the true duplicate pairs for later evaluation.
`record_entity_mapping.csv` is only included for debugging and should not be used as input for matching methods.

## Current status

The repository currently contains a small reproducible sample dataset. It is intended for testing the full pipeline before generating larger datasets for the actual experiments.

Next step: run a first PyJedAI smoke test on `patients_dirty.csv` and check whether the ground truth can be used correctly for Dirty ER evaluation.

