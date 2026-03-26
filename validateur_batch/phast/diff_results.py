#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Compare deux fichiers CSV (séparateur ;) sur un sous-ensemble de colonnes et
exporte uniquement les différences dans un fichier Excel.
"""

import argparse
import unicodedata
from pathlib import Path

import pandas as pd

KEEP_COLS = ["id", "active", "conceptId", "FSN", "term", "acceptabilityId"]
COMMON_COLS = ["id", "conceptId", "FSN"]
DIFF_COLS = ["term", "active", "acceptabilityId"]


def normalize_text(s: str, ignore_case: bool, ignore_accents: bool) -> str:
    """Normalise une chaîne selon les options de comparaison."""
    if s is None:
        s = ""
    if ignore_accents:
        # décomposition + suppression des diacritiques
        s = "".join(ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch) != "Mn")
    if ignore_case:
        s = s.lower()
    return s


def read_needed(path: Path) -> pd.DataFrame:
    """Lit un CSV en ne chargeant que les colonnes utiles (insensible à la casse des noms)."""
    df = pd.read_csv(
        path,
        sep=";",
        usecols=KEEP_COLS,
        dtype=str,
        encoding="utf-8-sig",
        low_memory=False,
    )

    # Nettoyage basique
    df["id"] = df["id"].astype(str).fillna(df["conceptId"] + '-' + df["term"])
    df = df[KEEP_COLS].astype(str).fillna("")
    return df


def compute_diff(
    old: pd.DataFrame,
    new: pd.DataFrame,
    ignore_case: bool = False,
    ignore_accents: bool = False,
) -> pd.DataFrame:
    """Construit la table des différences, avec colonnes old à gauche et new à droite + diff_type."""

    print(old.columns)
    print(len(old))
    print(new.columns)
    print(len(new))

    merged = old.merge(new, on=COMMON_COLS, how="outer", suffixes=("_old", "_new"), indicator=True)

    print(len(merged))
    print(merged.columns)
    print(merged.head(10))

    # Préparer colonnes pour la comparaison
    for c in [col for col in DIFF_COLS]:
        print(c)
        merged[f"{c}_old"] = merged.get(f"{c}_old", "").fillna("")
        merged[f"{c}_new"] = merged.get(f"{c}_new", "").fillna("")

    print(merged.columns)

    # Masque "changed" : comparaison vectorisée
    changed_mask = False
    for c in [c for c in DIFF_COLS]:
        left = merged[f"{c}_old"].astype(str)
        right = merged[f"{c}_new"].astype(str)

        changed_mask = changed_mask | (left != right)

    diff_type = merged["_merge"].map(
        {"left_only": "only_in_old", "right_only": "only_in_new", "both": "same"}
    ).astype(str)
    diff_type = diff_type.where(diff_type != "same", other=diff_type.where(~changed_mask, other="changed"))
    merged["diff_type"] = diff_type

    print(merged.columns)

    # Ne garder que les différences
    diff = merged[merged["diff_type"] != "same"].copy()

    # Colonnes dans l’ordre souhaité
    ordered_cols = COMMON_COLS
    for c in [c for c in DIFF_COLS]:
        ordered_cols = ordered_cols + [f"{c}_old"] + [f"{c}_new"]
    ordered_cols = ordered_cols + ["diff_type"]

    print(ordered_cols)
    diff = diff[ordered_cols].sort_values(["conceptId"])
    return diff


def main():
    parser = argparse.ArgumentParser(
        description="Comparer deux CSV (séparateur ;) et sortir un Excel contenant uniquement les différences."
    )
    parser.add_argument("old_csv", type=Path, help="Chemin vers l'ancien CSV (ex: check_results.csv)")
    parser.add_argument("new_csv", type=Path, help="Chemin vers le nouveau CSV (ex: check_results-nouv.csv)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("differences.xlsx"),
        help="Chemin du fichier Excel de sortie (par défaut: differences.xlsx)",
    )
    parser.add_argument(
        "--ignore-case",
        action="store_true",
        help="Ignorer la casse pour la comparaison de FSN et term",
    )
    parser.add_argument(
        "--ignore-accents",
        action="store_true",
        help="Ignorer les accents/diacritiques pour la comparaison de FSN et term",
    )
    args = parser.parse_args()

    # Lecture
    old = read_needed(args.old_csv)
    new = read_needed(args.new_csv)

    # Calcul différences
    diff = compute_diff(old, new, ignore_case=args.ignore_case, ignore_accents=args.ignore_accents)

    print (diff.head(10))

    # Résumé
    resume = (
        diff["diff_type"].value_counts(dropna=False).rename_axis("diff_type").reset_index(name="count")
    )

    # Écriture Excel
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(args.output, engine="openpyxl") as writer:
        diff.to_excel(writer, index=False, sheet_name="Differences")
        resume.to_excel(writer, index=False, sheet_name="Résumé")

    # Petit log en console
    print("✅ Export terminé :", args.output.resolve())
    print("— Lignes old :", len(old), "| Lignes new :", len(new), "| Différences :", len(diff))
    print(resume.to_string(index=False))


if __name__ == "__main__":
    main()