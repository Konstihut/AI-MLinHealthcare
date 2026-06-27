#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SYNTHEA_REPO="https://github.com/synthetichealth/synthea.git"
SYNTHEA_COMMIT="d02dcd65b0c8cd96d91ae7660f3570daf0fb41a1"

SEED=42
CLINICIAN_SEED=4242
REFERENCE_DATE=20260627
POPULATION=100

SYNTHEA_DIR="$ROOT_DIR/data/external/synthea"
RAW_DIR="$ROOT_DIR/data/raw/synthea_seed42_100"
SAMPLE_DIR="$ROOT_DIR/data/sample/synthea_seed42_100"

mkdir -p "$ROOT_DIR/data/external" "$ROOT_DIR/data/raw" "$ROOT_DIR/data/sample"

if [ ! -d "$SYNTHEA_DIR/.git" ]; then
  git clone "$SYNTHEA_REPO" "$SYNTHEA_DIR"
fi

git -C "$SYNTHEA_DIR" fetch origin "$SYNTHEA_COMMIT"
git -C "$SYNTHEA_DIR" checkout --detach "$SYNTHEA_COMMIT"

rm -rf "$RAW_DIR" "$SAMPLE_DIR"
mkdir -p "$SAMPLE_DIR"

cd "$SYNTHEA_DIR"
chmod +x run_synthea gradlew

./run_synthea -s "$SEED" -cs "$CLINICIAN_SEED" -p "$POPULATION" -r "$REFERENCE_DATE" \
  --exporter.csv.export=true \
  --exporter.fhir.export=false \
  --exporter.baseDirectory="$RAW_DIR"

cp "$RAW_DIR/csv/patients.csv" "$SAMPLE_DIR/patients.csv"
python -c "import pandas as pd; p='$SAMPLE_DIR/patients.csv'; df=pd.read_csv(p); df.sort_values('Id').to_csv(p, index=False)"

printf "Dataset: Synthea seed42 100 patient base sample\n" > "$SAMPLE_DIR/metadata.txt"
printf "Purpose: Clean base table for Dirty Entity Resolution experiments\n" >> "$SAMPLE_DIR/metadata.txt"
printf "Synthea repository: %s\n" "$SYNTHEA_REPO" >> "$SAMPLE_DIR/metadata.txt"
printf "Synthea commit: %s\n" "$SYNTHEA_COMMIT" >> "$SAMPLE_DIR/metadata.txt"
printf "Seed: %s\n" "$SEED" >> "$SAMPLE_DIR/metadata.txt"
printf "Clinician seed: %s\n" "$CLINICIAN_SEED" >> "$SAMPLE_DIR/metadata.txt"
printf "Population parameter: %s\n" "$POPULATION" >> "$SAMPLE_DIR/metadata.txt"
printf "Reference date: %s\n" "$REFERENCE_DATE" >> "$SAMPLE_DIR/metadata.txt"
printf "Location: Massachusetts\n" >> "$SAMPLE_DIR/metadata.txt"
printf "Raw output directory: data/raw/synthea_seed42_100\n" >> "$SAMPLE_DIR/metadata.txt"
printf "Committed sample file: data/sample/synthea_seed42_100/patients.csv\n" >> "$SAMPLE_DIR/metadata.txt"

python -c "import pandas as pd; p='$SAMPLE_DIR/patients.csv'; df=pd.read_csv(p); print('Created:', p); print('Shape:', df.shape); print('Columns:', list(df.columns)); print(df.head(3).to_string())"
