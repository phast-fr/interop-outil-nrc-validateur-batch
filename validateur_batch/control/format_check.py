import jsonpath
import numpy as np
import pandas as pd

from validateur_batch.object.server import INACTIVE_STATUS 
from typing import Dict, TYPE_CHECKING
import validateur_batch.control.verhoeff as verhoeff

if TYPE_CHECKING:
    from validateur_batch.object import batch, server

def _check_verhoeff(df: pd.DataFrame) -> pd.DataFrame:
    """Vérifie la validité des SCTID de concepts et descriptions à l'aide de l'algorithme de Verhoeff
    args:
        df: DataFrame à valider
    returns:
        DataFrame avec une colonne identifiant les lignes ayant un SCTID de concept ou de description
        invalide selon l'algorithme de Verhoeff
    """
    if "Concept ID" in df.columns:
        idx = df.loc[~df.loc[:, "Concept ID"].map(lambda x: verhoeff.validate(str(x)))].index
        if not idx.empty:
            df = pd.merge(df, pd.DataFrame(data={"E_concept_id_verhoeff": ["1"] * len(idx)},
                                           index=idx),
                          how="left", left_index=True, right_index=True, validate="1:1")
            
    if "Description ID" in df.columns:
        idx = df.loc[~df.loc[:, "Description ID"].map(lambda x: verhoeff.validate(str(x)))].index
        if not idx.empty:
            df = pd.merge(df, pd.DataFrame(data={"E_description_id_verhoeff": ["1"] * len(idx)},
                                           index=idx),
                          how="left", left_index=True, right_index=True, validate="1:1")
            
    if "Association Target ID1" in df.columns:
        idx = df.loc[~df.loc[:, "Association Target ID1"].map(lambda x: verhoeff.validate(str(x)))].index
        if not idx.empty:
            df = pd.merge(df, pd.DataFrame(data={"E_association_target_id_verhoeff": ["1"] * len(idx)},
                                           index=idx),
                          how="left", left_index=True, right_index=True, validate="1:1")
            
    if "Description ID Or Term" in df.columns:
        idx = df.loc[~df.loc[:, "Description ID Or Term"].map(lambda x: verhoeff.validate(str(x)))].index
        if not idx.empty:
            df = pd.merge(df, pd.DataFrame(data={"E_description_id_or_term_verhoeff": ["1"] * len(idx)},
                                           index=idx),
                          how="left", left_index=True, right_index=True, validate="1:1")
            
    if "New Replacement Description ID" in df.columns:
        idx = df.loc[~df.loc[:, "New Replacement Description ID"].map(lambda x: verhoeff.validate(str(x)))].index
        if not idx.empty:
            df = pd.merge(df, pd.DataFrame(data={"E_new_replacement_description_id_verhoeff": ["1"] * len(idx)},
                                           index=idx),
                          how="left", left_index=True, right_index=True, validate="1:1")   
              
    return df


def _find_empty_cell(df: pd.DataFrame, type: "batch.BATCH_TYPE") -> pd.DataFrame:
    """Cherche des cellules vides ou NaN dans le DataFrame.

    args:
        df: DataFrame à valider
        type: Type de batch

    returns:
        DataFrame avec une colonne identifiant les lignes ayant une cellule vide ou
        contenant un NaN
    """
    match  type:
        case "VAL":
            col = ["Concept ID", "FSN"]
        case "ADD":
            col = ["Concept ID", "Translated Term", "Language Code",
                   "Case significance", "Type", "Language reference set",
                   "Acceptability"]
        case "CHG":
            col = ["Description ID", "Case significance", "Type",
                   "Language reference set", "Acceptability"]
        case "INA":
            col = ["Description ID Or Term", "Inactivation Reason"]
        case "REP":
            col = ["Concept ID", "Description ID", "Inactivation Reason"]

    empty = {int(i) for i in np.where(pd.isnull(df.loc[:, col]))[0]}
    nan = {int(i) for i in np.where(df.loc[:, col].map(lambda x: x == ""))[0]}
    idx = list(empty.union(nan))

    if idx:
        df = pd.merge(df, pd.DataFrame(data={"W_cellule_vide": ["1"] * len(idx)},
                                       index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _sctid_is_inactive(json: Dict) -> str:
    """Vérifie si le concept est inactif

    args:
        json: Résultat de l'opération lookup

    returns:
        "1" si le concept est inactif ou une string vide dans le cas contraire
    """
    p = list(
        jsonpath.query("$.parameter[?@name == 'property'].part[?@valueCode == 'inactive']", json).pointers() # noqa
    )[0]

    return "" if next(filter(
        lambda x: x["name"] == "value", p.resolve_parent(json)[0]))["valueBoolean"] is False else "1" # noqa


def _validate_sctid(df: pd.DataFrame, fts: "server.Server") -> pd.DataFrame:
    """Valide les SCTID de concepts et ajoute les FSN de chaque concept
    args:
        df: DataFrame à valider
        fts: Serveur de Terminologies FHIR à utiliser
    returns:
        DataFrame avec 2 colonnes identifiant : les SCTID de concepts inactifs et les
        FSN
    """
    status = [fts.get_status(sctid) if sctid else "" for sctid in df.loc[:, "Concept ID"]]
    inactive = ["1" if s == INACTIVE_STATUS else "" for s in status]

    if "1" in inactive:
        df.loc[:, "E_concept_inactif"] = inactive

    return df

def _duplicated_term(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Vérifie s'il existe des termes dupliqués dans le fichier

    args:
        df: DataFrame à valider
        col: Nom de la colonne à vérifier dans `df`

    returns:
        DataFrame avec une colonne identifiant les lignes ayant un terme dupliqué
    """
    idx = df.loc[df.duplicated(col, keep=False),].index

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"W_terme_dupliqué": ["1"] * len(idx)},
                                       index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_language_code(df: pd.DataFrame) -> pd.DataFrame:
    """Vérifie la valeur de la colonne Language Code

    args:
        df: DataFrame à valider

    returns:
        DataFrame avec une colonne identifiant les lignes ayant une valeur incorrecte
        dans la colonne Language Code
    """
    if "Language Code" not in df.columns:
        return df

    idx = df.loc[df.loc[:, "Language Code"] != "fr"].index

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"E_language_code": ["1"] * len(idx)},
                                       index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_case_significance(df: pd.DataFrame) -> pd.DataFrame:
    """Vérifie la valeur de la colonne Case significance

    args:
        df: DataFrame à valider

    returns:
        DataFrame avec une colonne identifiant les lignes ayant une valeur incorrecte
        dans la colonne Case significance
    """
    if "Case significance" not in df.columns:
        return df

    idx = df.loc[~df.loc[:, "Case significance"].isin(["ci", "cI", "CS"])].index

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"E_case_significance": ["1"] * len(idx)},
                                       index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_type(df: pd.DataFrame) -> pd.DataFrame:
    """Vérifie la valeur de la colonne Type

    args:
        df: DataFrame à valider

    returns:
        DataFrame avec une colonne identifiant les lignes ayant une valeur incorrecte
        dans la colonne Type
    """
    if "Type" not in df.columns:
        return df

    idx = df.loc[~df.loc[:, "Type"].isin(["SYNONYM", "DEF"])].index

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"E_type": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_language_refset(df: pd.DataFrame) -> pd.DataFrame:
    """Vérifie la valeur de la colonne Language reference set

    args:
        df: DataFrame à valider

    returns:
        DataFrame avec une colonne identifiant les lignes ayant une valeur incorrecte
        dans la colonne Language reference set
    """
    if "Language reference set" not in df.columns:
        return df

    idx = df.loc[df.loc[:, "Language reference set"] != "French"].index

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"E_language_refset": ["1"] * len(idx)},
                                       index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_acceptability(df: pd.DataFrame) -> pd.DataFrame:
    """Vérifie la valeur de la colonne Acceptability

    args:
        df: DataFrame à valider

    returns:
        DataFrame avec une colonne identifiant les lignes ayant une valeur incorrecte
        dans la colonne Acceptability
    """
    if "Acceptability" not in df.columns:
        return df

    idx = df.loc[~df.loc[:, "Acceptability"].isin(["PREFERRED", "ACCEPTABLE"])].index

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"E_acceptability": ["1"] * len(idx)},
                                       index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_inactivation_reason(df: pd.DataFrame) -> pd.DataFrame:
    """Vérifie la valeur de la colonne Inactivation Reason

    args:
        df: DataFrame à valider

    returns:
        DataFrame avec une colonne identifiant les lignes ayant une valeur incorrecte
        dans la colonne Inactivation Reason
    """
    if "Inactivation Reason" not in df.columns:
        return df

    reason = ["Not semantically equivalent", "Outdated",
              "Grammatical description error", "Non-conformance to editorial policy"]
    idx = df.loc[~df.loc[:, "Inactivation Reason"].isin(reason)].index

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"E_inactivation_reason": ["1"] * len(idx)},
                                       index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_association_target(df: pd.DataFrame, fts: "server.Server") -> pd.DataFrame:
    """Vérifie la présence d'un concept cible dans le cas d'une description
    inactivée pour la raison "Not semantically equivalent"
    args:
        df: DataFrame à valider
        fts: Serveur de Terminologies FHIR à utiliser
    returns:
        DataFrame avec une colonne identifiant les lignes ne définissant pas de concept
        cible
    """
    if "Association Target ID1" not in df.columns:
        return df
    idx = df.loc[(df.loc[:, "Inactivation Reason"] == "Not semantically equivalent")
                 & ((df.loc[:, "Association Target ID1"] == "")
                    | pd.isnull(df.loc[:, "Association Target ID1"]))].index
    
    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"E_association_target": ["1"] * len(idx)},
                                       index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")
        
    status = [fts.get_status(sctid) if sctid else ""
            for sctid in df.loc[:, "Association Target ID1"]]
    
    inactive = ["1" if s == INACTIVE_STATUS else "" for s in status]

    if "1" in inactive:
        df.loc[:, "E_association_target_inactive"] = inactive
    return df


def check_pt(df: pd.DataFrame) -> pd.DataFrame:
    """Vérifie que chaque concept possède un seul PT.
    args:
        df: DataFrame à valider
    returns:
        DataFrame du fichier avec une colonne identifiant les concepts ayant moins ou
        plus d'un PT
    """
    df.loc[:, "E_multiple_pt"] = [""] * len(df)

    pt = df.loc[(df.loc[:, "acceptabilityId"] == "PREFERRED") & (df.loc[:, "active"] == "1"),
                ["conceptId", "acceptabilityId"]]
    
    error = pt[pt.duplicated("conceptId") == True]  # noqa

    if len(error) > 0:
        error.loc[:, "E_multiple_pt"] = ["1"] * len(error)
        df.update(error)

    return df

def run_format_check(df: pd.DataFrame, type: "batch.BATCH_TYPE",
                     fts: "server.Server") -> pd.DataFrame:
    """Lance l'ensemble des contrôles sur le respect du format.

    args:
        df: DataFrame à valider
        type: Type de batch
        fts: Serveur de Terminologies FHIR à utiliser

    returns:
        Fichier avec les résultats des contrôles
    """
    # Contrôle de la validité des SCTID à l'aide de l'algorithme de Verhoeff
    df = _check_verhoeff(df)

    # Contrôle de la présence de cellules vides
    df = _find_empty_cell(df, type)
    
    if type in ["ADD", "REP"]:
        # Contrôle des SCTID & ajout des FSN
        df = _validate_sctid(df, fts)
        # Contrôle de la présence de doublons
        col = "Translated Term" if type == "ADD" else "New Translated Term"
        df = _duplicated_term(df, col)

    # Contrôles des valeurs de colonnes spécifiques
    df = _check_language_code(df)
    df = _check_case_significance(df)
    df = _check_type(df)
    df = _check_language_refset(df)
    df = _check_acceptability(df)
    df = _check_inactivation_reason(df)
    df = _check_association_target(df, fts)

    return df
