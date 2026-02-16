import os.path as op
import pandas as pd

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from validateur_batch.object import batch


CASE = {
    "900000000000448009": "ci",
    "900000000000017005": "CS",
    "900000000000020002": "cI"
}

ACCEPT = {
    "900000000000548007": "PREFERRED",
    "900000000000549004": "ACCEPTABLE"
}


def read_snapshot(snapshot: str, date: str,
                  list_batch: List["batch.Batch"]) -> pd.DataFrame:
    """Lecture de la Snapshot de l'édition française

    args:
        snapshot: Chemin vers le dossier de la snapshot
        date : Date de release de la snapshot
        list_batch: Liste des batchs à valider

    returns:
        DataFrame représentant les concepts de l'édition FR inclus dans le périmètre
        des batchs
    """
    # Vérification du dossier Snapshot
    if op.basename(op.normpath(snapshot)) != "Snapshot":
        raise ValueError("Le chemin ne pointe pas vers le dossier Snapshot")
    p = {
        "concept": op.join(snapshot, f"Terminology/sct2_Concept_Snapshot_FR1000315_{date}.txt"), # noqa
        "desc_fr": op.join(snapshot, f"Terminology/sct2_Description_Snapshot-fr_FR1000315_{date}.txt"), # noqa
        "desc_en": op.join(snapshot, f"Terminology/sct2_Description_Snapshot-en_FR1000315_{date}.txt"), # noqa
        "lang": op.join(snapshot, f"Refset/Language/der2_cRefset_LanguageSnapshot-fr_FR1000315_{date}.txt") # noqa
    }

    print("Lecture des concepts...", end="\r")
    # Lecture des concepts
    concept = pd.read_csv(p["concept"], sep="\t", usecols=["id", "active"],
                          dtype={"id": str, "active": pd.CategoricalDtype(["1", "0"])})
    concept = concept.loc[concept.loc[:, "active"] == "1"]
    print("Lecture des concepts - OK")

    print("Lecture des descriptions...", end="\r")
    # Lecture des descriptions françaises
    desc = pd.read_csv(p["desc_fr"], sep="\t", quoting=3, na_filter=False,
                       usecols=["id", "active", "conceptId", "typeId", "term",
                                "caseSignificanceId"],
                       dtype={"id": str, "active": pd.CategoricalDtype(["1", "0"]),
                              "conceptId": str, "typeId": str, "term": str},
                       converters={"caseSignificanceId": lambda x: CASE.get(x)})
    desc = desc.loc[(desc.loc[:, "conceptId"].isin(concept.loc[:, "id"]))
                    & (desc.loc[:, "typeId"] == "900000000000013009")
                    & (desc.loc[:, "active"] == "1")]
    print("Lecture des descriptions - OK")

    # Lecture des acceptabilités
    print("Lecture des language refset...", end="\r")
    lang = pd.read_csv(p["lang"], sep="\t", na_filter=False,
                       usecols=["referencedComponentId", "acceptabilityId"],
                       dtype={"referencedComponentId": str},
                       converters={"acceptabilityId": lambda x: ACCEPT.get(x)})
    print("Lecture des language refset - OK")

    print("Préparation du DataFrame...", end="\r")
    # Fusion & filtre par rapport au périmètre des batchs
    desc = pd.merge(desc, lang, how="left", left_on="id",
                    right_on="referencedComponentId")
    desc.drop(["typeId", "referencedComponentId"], axis=1, inplace=True)

    # Récupérer les concepts ID du non modifié + batchs d'addition et remplacement
    scope = set().union(*[
        b.df.loc[:, "Concept ID"] for b in list_batch if b.type in ["ADD", "REP", "VAL"]
    ])
    # Récupérer les concepts ID des batchs de changement et inactivation + les concepts
    # ID des descriptions de remplacements d'un batch de remplacement
    scope_d = set().union(*[
        b.df.loc[:, "Description ID"] for b in list_batch if b.type == "CHG"
    ])
    scope_d = scope_d.union(*[
        b.df.loc[:, "Description ID Or Term"] for b in list_batch if b.type == "INA"
    ])
    scope = scope.union(desc.loc[desc.loc[:, "id"].isin(scope_d), "conceptId"])
    print("Préparation du DataFrame - OK", end="\r")

    return desc.loc[desc.loc[:, "conceptId"].isin(scope)]
