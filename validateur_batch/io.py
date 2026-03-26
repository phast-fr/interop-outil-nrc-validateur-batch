import os.path as op
import pandas as pd

from typing import List

from validateur_batch.object import batch
from validateur_batch.scope import Scope



CASE = {
    "900000000000448009": "ci",
    "900000000000017005": "CS",
    "900000000000020002": "cI"
}

ACCEPT = {
    "900000000000548007": "PREFERRED",
    "900000000000549004": "ACCEPTABLE"
}

def concepts_in_delivery(list_batch: List["batch.Batch"],
                         desc : pd.DataFrame) -> set:
    """
    Ensemble des concepts contenus dans la livraison

    args:
        list_batch: Liste des batchs à valider
        desc : dataframe des descriptions dans l'édition FR

    returns:
        set des concept IDs contenus dans la livraison
    """
    # Récupérer les concepts ID du non modifié + batchs d'addition et remplacement
    scope_delivery = set().union(*[
        b.df.loc[:, "Concept ID"] for b in list_batch if b.type in ["ADD", "REP", "VAL"]
    ])

    # Récupérer les concepts ID des batchs de changement et inactivation + les concepts
    # ID des descriptions de remplacements d'un batch de remplacement
    scope_modifs_d = set().union(*[
        b.df.loc[:, "Description ID"] for b in list_batch if b.type == "CHG"
    ])
    scope_modifs_d = scope_modifs_d.union(*[
        b.df.loc[:, "Description ID Or Term"] for b in list_batch if b.type == "INA"
    ])
    scope_delivery = scope_delivery.union(desc.loc[desc.loc[:, "id"].isin(scope_modifs_d), "conceptId"])

    print(f"{len(scope_delivery)} concepts dans la livraison")

    return scope_delivery

def read_active_desc_in_fr_ed(snapshot: str, date: str) -> pd.DataFrame:
    """Lecture de la Snapshot de l'édition française

    args:
        snapshot: Chemin vers le dossier de la snapshot
        date : Date de release de la snapshot

    returns:
        DataFrame contenant toutes les descriptions actives de l'edition nationale fr
    """
    # Vérification du dossier Snapshot
    if op.basename(op.normpath(snapshot)) != "Snapshot":
        raise ValueError("Le chemin ne pointe pas vers le dossier Snapshot")
    p = {
        "concept": op.join(
            snapshot, f"Terminology/sct2_Concept_Snapshot_FR1000315_{date}.txt"
        ),  # noqa
        "desc_fr": op.join(
            snapshot,
            f"Terminology/sct2_Description_Snapshot-fr_FR1000315_{date}.txt",
        ),  # noqa
        "desc_en": op.join(
            snapshot,
            f"Terminology/sct2_Description_Snapshot-en_FR1000315_{date}.txt",
        ),  # noqa
        "lang": op.join(
            snapshot,
            f"Refset/Language/der2_cRefset_LanguageSnapshot-fr_FR1000315_{date}.txt",
        ),  # noqa
    }

    print("Lecture des concepts...", end="\r")
    # Lecture des concepts
    concept = pd.read_csv(
        p["concept"],
        sep="\t",
        usecols=["id", "active"],
        dtype={"id": str, "active": pd.CategoricalDtype(["1", "0"])},
    )
    concept = concept.loc[concept.loc[:, "active"] == "1"]
    print("Lecture des concepts - OK")

    print("Lecture des descriptions...", end="\r")
    # Lecture des descriptions françaises
    desc = pd.read_csv(
        p["desc_fr"],
        sep="\t",
        quoting=3,
        na_filter=False,
        usecols=[
            "id",
            "active",
            "conceptId",
            "typeId",
            "term",
            "caseSignificanceId",
        ],
        dtype={
            "id": str,
            "active": pd.CategoricalDtype(["1", "0"]),
            "conceptId": str,
            "typeId": str,
            "term": str,
        },
        converters={"caseSignificanceId": lambda x: CASE.get(x)},
    )
    desc = desc.loc[
        (desc.loc[:, "conceptId"].isin(concept.loc[:, "id"]))
        & (desc.loc[:, "typeId"] == "900000000000013009")
        & (desc.loc[:, "active"] == "1")
    ]
    print("Lecture des descriptions - OK")

    # Lecture des acceptabilités
    print("Lecture des language refset...", end="\r")
    lang = pd.read_csv(
        p["lang"],
        sep="\t",
        na_filter=False,
        usecols=["referencedComponentId", "acceptabilityId"],
        dtype={"referencedComponentId": str},
        converters={"acceptabilityId": lambda x: ACCEPT.get(x)},
    )
    print("Lecture des language refset - OK")

    print("Préparation du DataFrame...", end="\r")
    # Fusion & filtre par rapport au périmètre des batchs
    desc = pd.merge(
        desc, lang, how="left", left_on="id", right_on="referencedComponentId"
    )
    desc.drop(["typeId", "referencedComponentId"], axis=1, inplace=True)

    return desc

def select_desc(
    desc_act_fr: pd.DataFrame,
    list_batch: List["batch.Batch"],
    scope_of_order: Scope,
) -> pd.DataFrame:
    """Lectures des descriptions de l'édition nationale fr dans le scope

    args:
        descr_act_fr: Dataframe des descriptions actives dans l'édition nationale fr
        list_batch: Liste des batchs à valider
        scope_of_order : Périmètre officiel de la commande

    returns:
        DataFrame représentant les concepts de l'édition FR inclus dans le périmètre
        des batchs
    """

    scope_delivery = concepts_in_delivery(list_batch, desc_act_fr)

    if scope_of_order:
        print(
            f"{len(scope_of_order.full_scope_df['conceptId'])} concepts dans le périmètre commandé."
        )
        scope_analysis = scope_delivery.union(
            scope_of_order.full_scope_df["conceptId"]
        )
        print(
            f"{len(scope_analysis)} concepts après union commande et livraison"
        )
    else:
        scope_analysis = scope_delivery

    descriptions_in_scope = desc_act_fr.loc[
        desc_act_fr.loc[:, "conceptId"].isin(scope_analysis)
    ]

    descriptions_in_scope["source"] = "order"
    descriptions_in_scope.loc[
        descriptions_in_scope["conceptId"].isin(scope_delivery), "source"
    ] = "delivery"

    descriptions_in_scope["_type_"] = ""

    print("Préparation du DataFrame - OK", end="\r")

    return descriptions_in_scope
