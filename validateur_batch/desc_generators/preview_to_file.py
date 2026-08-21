import logging
from pathlib import Path
import pandas as pd
import csv
logger = logging.getLogger(__name__)

def write_add_file(add_file_path: Path, new_descriptions: pd.DataFrame):
    """ Écrit un fichier "ADD" au format du template SNOMED Managed Services

    Args:
        add_file_path (Path): chemin vers le fichier csv à écrire
        new_descriptions (pd.DataFrame): dataframe des descriptions à ajouter
    """

    df = pd.DataFrame(
        {
            "Concept ID": new_descriptions["conceptId"],
            "GB/US FSN Term (For reference only)": new_descriptions["FSN"],
            "Preferred Term (For reference only)": new_descriptions["PT_EN"],
            "Translated Term": new_descriptions["term"],
            "Language Code": "fr",
            "Case significance": new_descriptions["caseSignificanceId"],
            "Type": "SYNONYM",
            "Language reference set" : "French",
            "Acceptability":  new_descriptions["acceptabilityId"]
        }
    )

    df.to_csv(add_file_path, index=False, sep=";", quoting=csv.QUOTE_NONE, encoding='utf-8')


def write_val_file(val_file_path: Path, preview: pd.DataFrame):
    """ Écrit un fichier "VAL" au format prévu en livraison, à partir du preview mis à jour avec les descriptions générées

    Args:
        val_file_path (Path): chemin vers le fichier csv à écrire
        preview (pd.DataFrame): dataframe du preview mis à jour avec les descriptions générées
    """

    mask = (preview["_type_"] == "VAL")
    df = pd.DataFrame(
        {
            "Concept ID": preview.loc[mask, "conceptId"],
            "FSN": preview.loc[mask, "FSN"],
        }
    )
    # `preview` a une ligne par description existante : un concept ayant
    # plusieurs descriptions actives (PT + synonymes) apparaît donc plusieurs
    # fois avec le même Concept ID/FSN. VAL est une déclaration au niveau
    # concept, donc on ne garde qu'une seule occurrence.
    df = df.drop_duplicates(subset="Concept ID")

    df.to_csv(val_file_path, index=False, sep=";", quoting=csv.QUOTE_NONE, encoding='utf-8')
    df.to_excel(Path(val_file_path).with_suffix(".xlsx"), index=False)