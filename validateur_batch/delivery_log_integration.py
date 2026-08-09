"""Intègre les erreurs de reconditionnement REMP dans le classeur Logs.

Ajoute un onglet ``Logs REMP`` au classeur ``Logs *.xlsx`` produit par l'outil
de transformation, à partir du ``conversion_errors.csv`` généré par
:func:`validateur_batch.delivery_converter.prepare_delivery_inputs`. Seules
les lignes en erreur sont reprises ; le classeur Logs original n'est modifié
que par l'ajout de ce nouvel onglet.
"""

from __future__ import annotations

import argparse

import pandas as pd
from openpyxl import load_workbook

LOG_HEADERS = ["ConceptId", "FsnEn", "Message", "Type", "N° ligne", "Fichier"]


def append_delivery_errors_to_log(
    errors_csv: str, logs_xlsx: str, sheet_name: str = "Logs REMP"
) -> None:
    """Ajoute les erreurs de reconditionnement REMP dans le classeur Logs."""
    errors = pd.read_csv(errors_csv, sep=";", dtype=str, na_filter=False)

    workbook = load_workbook(logs_xlsx)
    if sheet_name in workbook.sheetnames:
        del workbook[sheet_name]
    sheet = workbook.create_sheet(sheet_name)
    sheet.append(LOG_HEADERS)
    for _, row in errors.iterrows():
        sheet.append(
            [
                row.get("conceptId", ""),
                "",
                row.get("message", ""),
                "ERROR",
                row.get("row", ""),
                row.get("file", ""),
            ]
        )
    workbook.save(logs_xlsx)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(
        description=(
            "Ajoute les erreurs de reconditionnement REMP (conversion_errors.csv) "
            "dans un onglet dédié du classeur Logs de l'outil de transformation."
        )
    )
    cli.add_argument("errors_csv", help="Chemin vers conversion_errors.csv")
    cli.add_argument("logs_xlsx", help="Chemin vers le classeur Logs *.xlsx")
    cli.add_argument(
        "--sheet_name", default="Logs REMP", help="Nom de l'onglet à créer/remplacer"
    )
    args = cli.parse_args()

    append_delivery_errors_to_log(args.errors_csv, args.logs_xlsx, args.sheet_name)
    print(f"Erreurs REMP intégrées dans {args.logs_xlsx} (onglet {args.sheet_name!r})")
