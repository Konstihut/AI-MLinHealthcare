#!/usr/bin/env python3

from __future__ import annotations

import argparse
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd


ER_COLUMNS = [
    "BIRTHDATE",
    "DEATHDATE",
    "PREFIX",
    "FIRST",
    "MIDDLE",
    "LAST",
    "SUFFIX",
    "MAIDEN",
    "MARITAL",
    "RACE",
    "ETHNICITY",
    "GENDER",
    "BIRTHPLACE",
    "ADDRESS",
    "CITY",
    "STATE",
    "COUNTY",
    "ZIP",
]

TYPO_FIELDS = [
    "FIRST",
    "MIDDLE",
    "LAST",
    "MAIDEN",
    "BIRTHPLACE",
    "ADDRESS",
    "CITY",
]

MISSING_FIELDS = [
    "PREFIX",
    "MIDDLE",
    "SUFFIX",
    "MAIDEN",
    "MARITAL",
    "ADDRESS",
    "CITY",
    "ZIP",
]

LETTERS = "abcdefghijklmnopqrstuvwxyz"


def is_missing(value: object) -> bool:
    return pd.isna(value) or str(value).strip() == ""


def values_differ(old_value: object, new_value: object) -> bool:
    if is_missing(old_value) and is_missing(new_value):
        return False
    return str(old_value) != str(new_value)


def validate_rate(name: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0.0 and 1.0, got {value}.")


def normalize_zip(value: object) -> object:
    if is_missing(value):
        return pd.NA

    text = str(value).strip()

    if text.endswith(".0"):
        text = text[:-2]

    return text


def random_character(rng: np.random.Generator, uppercase: bool = False) -> str:
    char = rng.choice(list(LETTERS))
    return char.upper() if uppercase else char


def apply_char_edit(value: object, rng: np.random.Generator) -> object:
    """Apply one Febrl-style character edit to a string value."""
    if is_missing(value):
        return value

    text = str(value)
    if len(text) == 0:
        return value

    operation = rng.choice(["delete", "insert", "substitute", "transpose"])

    if operation == "delete" and len(text) > 1:
        pos = int(rng.integers(0, len(text)))
        return text[:pos] + text[pos + 1 :]

    if operation == "insert":
        pos = int(rng.integers(0, len(text) + 1))
        char = random_character(rng)
        return text[:pos] + char + text[pos:]

    if operation == "substitute":
        pos = int(rng.integers(0, len(text)))
        old_char = text[pos]
        new_char = random_character(rng, uppercase=old_char.isupper())
        return text[:pos] + new_char + text[pos + 1 :]

    if operation == "transpose" and len(text) > 1:
        pos = int(rng.integers(0, len(text) - 1))
        chars = list(text)
        chars[pos], chars[pos + 1] = chars[pos + 1], chars[pos]
        return "".join(chars)

    return text


def perturb_zip(value: object, rng: np.random.Generator) -> object:
    if is_missing(value):
        return value

    text = str(value).split(".")[0]
    digits = list(text)

    digit_positions = [i for i, char in enumerate(digits) if char.isdigit()]
    if not digit_positions:
        return value

    pos = int(rng.choice(digit_positions))
    old_digit = digits[pos]
    new_digit = str(int(rng.integers(0, 10)))

    if new_digit == old_digit:
        new_digit = str((int(old_digit) + 1) % 10)

    digits[pos] = new_digit
    return "".join(digits)


def perturb_date(value: object, rng: np.random.Generator) -> object:
    if is_missing(value):
        return value

    date = pd.to_datetime(value, errors="coerce")
    if pd.isna(date):
        return value

    shift_days = int(rng.choice([-3, -2, -1, 1, 2, 3]))
    return (date + pd.Timedelta(days=shift_days)).strftime("%Y-%m-%d")


def corrupt_row(
    row: pd.Series,
    rng: np.random.Generator,
    typo_rate: float,
    missing_rate: float,
    date_error_rate: float,
    zip_error_rate: float,
) -> pd.Series:
    corrupted = row.copy()
    changed = False

    for field in TYPO_FIELDS:
        if field in corrupted.index and rng.random() < typo_rate:
            old_value = corrupted[field]
            new_value = apply_char_edit(old_value, rng)
            corrupted[field] = new_value
            changed = changed or values_differ(old_value, new_value)

    for field in MISSING_FIELDS:
        if field in corrupted.index and rng.random() < missing_rate:
            if not is_missing(corrupted[field]):
                corrupted[field] = pd.NA
                changed = True

    if "BIRTHDATE" in corrupted.index and rng.random() < date_error_rate:
        old_value = corrupted["BIRTHDATE"]
        new_value = perturb_date(old_value, rng)
        corrupted["BIRTHDATE"] = new_value
        changed = changed or values_differ(old_value, new_value)

    if "ZIP" in corrupted.index and rng.random() < zip_error_rate:
        old_value = corrupted["ZIP"]
        new_value = perturb_zip(old_value, rng)
        corrupted["ZIP"] = new_value
        changed = changed or values_differ(old_value, new_value)

    # Ensure that every artificial duplicate differs from its original at least once.
    if not changed:
        for fallback_field in ["LAST", "FIRST", "ADDRESS", "CITY"]:
            if fallback_field in corrupted.index and not is_missing(corrupted[fallback_field]):
                old_value = corrupted[fallback_field]
                new_value = apply_char_edit(old_value, rng)
                corrupted[fallback_field] = new_value
                changed = values_differ(old_value, new_value)
                if changed:
                    break

    if not changed:
        raise RuntimeError("Failed to create a changed duplicate record.")

    return corrupted


def build_ground_truth(mapping: pd.DataFrame) -> pd.DataFrame:
    pairs = []

    for _, group in mapping.groupby("entity_id"):
        record_ids = sorted(group["record_id"].tolist())
        if len(record_ids) < 2:
            continue

        for record_id_1, record_id_2 in combinations(record_ids, 2):
            pairs.append(
                {
                    "record_id_1": record_id_1,
                    "record_id_2": record_id_2,
                }
            )

    return pd.DataFrame(pairs)


def create_dirty_dataset(
    input_path: Path,
    output_dir: Path,
    seed: int,
    duplicate_rate: float,
    typo_rate: float,
    missing_rate: float,
    date_error_rate: float,
    zip_error_rate: float,
) -> None:
    rng = np.random.default_rng(seed)

    validate_rate("duplicate_rate", duplicate_rate)
    validate_rate("typo_rate", typo_rate)
    validate_rate("missing_rate", missing_rate)
    validate_rate("date_error_rate", date_error_rate)
    validate_rate("zip_error_rate", zip_error_rate)

    clean = pd.read_csv(input_path, dtype=str)
    available_columns = [column for column in ER_COLUMNS if column in clean.columns]

    if not available_columns:
        raise ValueError("No expected ER columns found in input dataset.")

    clean_er = clean[available_columns].copy()

    if "ZIP" in clean_er.columns:
        clean_er["ZIP"] = clean_er["ZIP"].apply(normalize_zip)

    n_clean = len(clean_er)
    n_duplicates = int(round(n_clean * duplicate_rate))

    if n_duplicates < 1:
        raise ValueError("duplicate_rate is too small; it creates zero duplicates.")

    duplicate_indices = rng.choice(n_clean, size=n_duplicates, replace=False)

    records = []
    mapping_rows = []

    for idx, row in clean_er.iterrows():
        record_id = f"P{idx:06d}"
        entity_id = f"E{idx:06d}"

        record = row.to_dict()
        record["record_id"] = record_id
        records.append(record)

        source_synthea_id = clean.loc[idx, "Id"] if "Id" in clean.columns else idx
        mapping_rows.append(
            {
                "record_id": record_id,
                "entity_id": entity_id,
                "source_synthea_id": source_synthea_id,
                "is_artificial_duplicate": False,
            }
        )

    for idx in sorted(duplicate_indices):
        record_id = f"P{idx:06d}_D1"
        entity_id = f"E{idx:06d}"

        corrupted = corrupt_row(
            clean_er.loc[idx],
            rng=rng,
            typo_rate=typo_rate,
            missing_rate=missing_rate,
            date_error_rate=date_error_rate,
            zip_error_rate=zip_error_rate,
        )

        record = corrupted.to_dict()
        record["record_id"] = record_id
        records.append(record)

        source_synthea_id = clean.loc[idx, "Id"] if "Id" in clean.columns else idx
        mapping_rows.append(
            {
                "record_id": record_id,
                "entity_id": entity_id,
                "source_synthea_id": source_synthea_id,
                "is_artificial_duplicate": True,
            }
        )

    dirty = pd.DataFrame(records)
    dirty = dirty[["record_id"] + available_columns]

    # Shuffle rows reproducibly so duplicates are not placed directly below originals.
    dirty = dirty.iloc[rng.permutation(len(dirty))].reset_index(drop=True)

    mapping = pd.DataFrame(mapping_rows)
    ground_truth = build_ground_truth(mapping)

    output_dir.mkdir(parents=True, exist_ok=True)

    dirty_path = output_dir / "patients_dirty.csv"
    mapping_path = output_dir / "record_entity_mapping.csv"
    ground_truth_path = output_dir / "ground_truth.csv"
    metadata_path = output_dir / "metadata.txt"

    csv_kwargs = {"index": False, "lineterminator": "\n"}

    dirty.to_csv(dirty_path, **csv_kwargs)
    mapping.to_csv(mapping_path, **csv_kwargs)
    ground_truth.to_csv(ground_truth_path, **csv_kwargs)

    metadata = f"""Dataset: Dirty ER patient sample
Purpose: Dirty Entity Resolution dataset derived from Synthea patients.csv
Input file: {input_path}
Output directory: {output_dir}
Seed: {seed}
Clean records: {n_clean}
Artificial duplicates: {n_duplicates}
Total dirty records: {len(dirty)}
Ground-truth duplicate pairs: {len(ground_truth)}
Duplicate rate: {duplicate_rate}
Typo rate: {typo_rate}
Missing value rate: {missing_rate}
Date error rate: {date_error_rate}
ZIP error rate: {zip_error_rate}

Files:
- patients_dirty.csv: dirty ER dataset without hidden entity labels
- ground_truth.csv: true duplicate record pairs
- record_entity_mapping.csv: debug/evaluation mapping from record_id to entity_id

Note:
The dirty dataset intentionally excludes original unique identifiers such as Synthea Id, SSN, drivers license, and passport number. These fields would make the matching task unrealistically easy.
"""
    metadata_path.write_text(metadata, encoding="utf-8")

    print("Created dirty ER dataset")
    print("Input:", input_path)
    print("Output:", output_dir)
    print("Clean records:", n_clean)
    print("Artificial duplicates:", n_duplicates)
    print("Total dirty records:", len(dirty))
    print("Ground-truth pairs:", len(ground_truth))
    print("Dirty file:", dirty_path)
    print("Ground truth:", ground_truth_path)
    print("Mapping:", mapping_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a reproducible dirty ER dataset from a clean Synthea patients.csv file."
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/sample/synthea_seed42_100/patients.csv"),
        help="Input clean Synthea patients.csv file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/sample/dirty_er_seed42_100"),
        help="Output directory for the dirty ER dataset.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--duplicate-rate", type=float, default=0.30)
    parser.add_argument("--typo-rate", type=float, default=0.20)
    parser.add_argument("--missing-rate", type=float, default=0.10)
    parser.add_argument("--date-error-rate", type=float, default=0.05)
    parser.add_argument("--zip-error-rate", type=float, default=0.10)

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    create_dirty_dataset(
        input_path=args.input,
        output_dir=args.output_dir,
        seed=args.seed,
        duplicate_rate=args.duplicate_rate,
        typo_rate=args.typo_rate,
        missing_rate=args.missing_rate,
        date_error_rate=args.date_error_rate,
        zip_error_rate=args.zip_error_rate,
    )


if __name__ == "__main__":
    main()
