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

## Next step

The next step is to create a Python script that reads:

```text
data/sample/synthea_seed42_100/patients.csv
```

and generates a dirty Entity Resolution dataset with:

* duplicate patient records
* typographical errors
* missing values
* spelling variations
* ground-truth duplicate pairs

This dirty dataset will then be used to evaluate filtering and blocking methods with PyJedAI.

