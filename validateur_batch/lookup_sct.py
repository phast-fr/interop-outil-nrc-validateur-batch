"""Construction de l'onglet LOOKUP_SCT à partir du périmètre analysé et du RF2 FR.

Prend en entrée le ``scope_concepts.csv`` produit par ``main.py`` (option
``--scope``) et le RF2 de l'édition nationale française, et produit un CSV
avec les mêmes colonnes que l'onglet ``LOOKUP_SCT`` des workbooks de
traduction : FSN/PT anglais (repris du scope), puis PT, FSN et synonymes
acceptables français (Description ID et Case Significance inclus).
"""

from __future__ import annotations

import argparse
import csv
import os.path as op

import pandas as pd

from validateur_batch.io import ACCEPT, CASE

FSN_TYPE = "900000000000003001"
SYNONYM_TYPE = "900000000000013009"
MAX_SYNONYMS = 20

HEADERS = [
    "SCTID du concept",
    "English FSN (Int. Edition )",
    "DESCRIPTION ID du FSN anglais",
    "Case significance FSN ang",
    "English preferred Term(Int. Edition )",
    "DESCRIPTION ID du PT anglais",
    "Case significance PT ang",
    "Terme Préféré Français",
    "DESCRIPTION ID du terme préféré français",
    "Case significance PT français",
    "FSN Français",
    "DESCRIPTION ID du FSN français",
    "Case significance FSN  français",
]
for _i in range(1, MAX_SYNONYMS + 1):
    HEADERS += [
        f"Synonyme Acceptable FR {_i}",
        f"DESCRIPTION ID du synonyme {_i} acceptable français",
        f"Case significance SYNONYME ACCEPTABLE {_i} français",
    ]


def _read_fr_fsn_and_synonyms(snapshot: str, date: str) -> pd.DataFrame:
    """Lit les FSN et synonymes actifs de l'édition FR (RF2 + acceptabilité)."""
    if op.basename(op.normpath(snapshot)) != "Snapshot":
        raise ValueError("Le chemin ne pointe pas vers le dossier Snapshot")

    desc_path = op.join(
        snapshot, f"Terminology/sct2_Description_Snapshot-fr_FR1000315_{date}.txt"
    )
    lang_path = op.join(
        snapshot,
        f"Refset/Language/der2_cRefset_LanguageSnapshot-fr_FR1000315_{date}.txt",
    )

    desc = pd.read_csv(
        desc_path,
        sep="\t",
        quoting=3,
        na_filter=False,
        usecols=["id", "active", "conceptId", "typeId", "term", "caseSignificanceId"],
        dtype={
            "id": str,
            "active": pd.CategoricalDtype(["1", "0"]),
            "conceptId": str,
            "typeId": str,
            "term": object,
        },
        converters={"caseSignificanceId": lambda x: CASE.get(x)},
    )
    desc = desc.loc[
        (desc["active"] == "1") & desc["typeId"].isin([FSN_TYPE, SYNONYM_TYPE])
    ]

    lang = pd.read_csv(
        lang_path,
        sep="\t",
        na_filter=False,
        usecols=["referencedComponentId", "acceptabilityId"],
        dtype={"referencedComponentId": str},
        converters={"acceptabilityId": lambda x: ACCEPT.get(x)},
    )

    desc = pd.merge(
        desc, lang, how="left", left_on="id", right_on="referencedComponentId"
    )
    desc.drop(columns=["referencedComponentId"], inplace=True)
    return desc


def _concept_row(
    concept_id: str, fsn_en: str, pten_en: str, concept_desc: pd.DataFrame
) -> list:
    """Construit une ligne LOOKUP_SCT pour un concept à partir de ses descriptions FR."""
    fsn_fr = concept_desc.loc[concept_desc["typeId"] == FSN_TYPE]
    pt_fr = concept_desc.loc[
        (concept_desc["typeId"] == SYNONYM_TYPE)
        & (concept_desc["acceptabilityId"] == "PREFERRED")
    ]
    synonyms_fr = concept_desc.loc[
        (concept_desc["typeId"] == SYNONYM_TYPE)
        & (concept_desc["acceptabilityId"] == "ACCEPTABLE")
    ].sort_values("id")

    row = [concept_id, fsn_en, "", "", pten_en, "", ""]

    if not pt_fr.empty:
        pt = pt_fr.iloc[0]
        row += [pt["term"], pt["id"], pt["caseSignificanceId"]]
    else:
        row += ["", "", ""]

    if not fsn_fr.empty:
        fsn = fsn_fr.iloc[0]
        row += [fsn["term"], fsn["id"], fsn["caseSignificanceId"]]
    else:
        row += ["", "", ""]

    for i in range(MAX_SYNONYMS):
        if i < len(synonyms_fr):
            syn = synonyms_fr.iloc[i]
            row += [syn["term"], syn["id"], syn["caseSignificanceId"]]
        else:
            row += ["", "", ""]

    return row


def build_lookup_sct(
    scope_concepts_csv: str, snapshot: str, date: str, output_csv: str
) -> None:
    """Génère le CSV LOOKUP_SCT à partir d'un scope_concepts.csv et du RF2 FR."""
    scope = pd.read_csv(scope_concepts_csv, sep=";", dtype=str).drop_duplicates(
        subset="conceptId"
    )

    fr_desc = _read_fr_fsn_and_synonyms(snapshot, date)
    empty = fr_desc.iloc[0:0]
    by_concept = {concept_id: df for concept_id, df in fr_desc.groupby("conceptId")}

    rows = [
        _concept_row(
            concept["conceptId"],
            concept.get("fsn", ""),
            concept.get("pten", ""),
            by_concept.get(concept["conceptId"], empty),
        )
        for _, concept in scope.iterrows()
    ]

    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(HEADERS)
        writer.writerows(rows)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(
        description=(
            "Construit un CSV LOOKUP_SCT à partir de scope_concepts.csv "
            "(généré par main.py --scope) et du RF2 de l'édition française."
        )
    )
    cli.add_argument("scope_concepts", help="Chemin vers scope_concepts.csv")
    cli.add_argument("snapshot", help="Chemin vers le dossier Snapshot du RF2 français")
    cli.add_argument("date", help="Date de la release RF2 française (YYYYMMDD)")
    cli.add_argument("output", help="Chemin du CSV LOOKUP_SCT à générer")
    args = cli.parse_args()

    build_lookup_sct(args.scope_concepts, args.snapshot, args.date, args.output)
    print(f"LOOKUP_SCT généré : {args.output}")
