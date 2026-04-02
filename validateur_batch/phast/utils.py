import pandas as pd

SHORT_ACCEPTABILITY = {
    "PREFERRED": "PT",
    "ACCEPTABLE": "SA"
}
MAIN_COLUMNS = ['id', 'active', '_type_', 'conceptId', 'FSN', 'FSN_no_sem', 'term', 'caseSignificanceId', 'acceptabilityId', 'errors', 'selected_rules']


def combine_rule_selections (row:dict) -> str:
    """Construit une chaîne résumant les règles sélectionnées pour une description.

    args:
        row: Ligne du DataFrame (dict) représentant une description

    returns:
        Chaîne de la forme "terme (PT|SA): règle1 règle2 ...", ou pd.NA si aucune règle sélectionnée.
    """
    selected_keys = [key for key in row.keys() if key.startswith("S_") and row[key]=="1"]
    if len(selected_keys) > 0:
        selection = row["term"] + f" ({SHORT_ACCEPTABILITY[row['acceptabilityId']]})" + ": " + " ".join([key[2:] for key in selected_keys])
    else:
        selection = pd.NA
    return selection

def combine_rule_errors (row:dict) -> str:
    """Construit une chaîne résumant les erreurs détectées pour une description.

    args:
        row: Ligne du DataFrame (dict) représentant une description

    returns:
        Chaîne de la forme "terme (PT|SA): erreur1 erreur2 ...", ou pd.NA si aucune erreur.
    """
    error_keys = [key for key in row.keys() if (key not in MAIN_COLUMNS) and (not key.startswith("S_")) and (not key.startswith("E_") and row[key]=="1")]
    if len(error_keys) > 0:
        errors = row["term"] + f" ({SHORT_ACCEPTABILITY[row['acceptabilityId']]})" + ": " + " ".join(error_keys)
    else:
        errors = pd.NA
    return errors

def aggregate_combined(values):
    """Concatène des valeurs non-nulles avec le séparateur ' | '.

    args:
        values: Itérable de valeurs (str ou pd.NA)

    returns:
        Chaîne des valeurs non-nulles jointes par ' | '.
    """
    return ' | '.join([v for v in values if pd.notna(v)])


def combine_results(check_result: pd.DataFrame) -> pd.DataFrame:
    """Agrège les résultats de contrôle par concept.

    args:
        check_result: DataFrame des résultats de contrôle au niveau description

    returns:
        DataFrame agrégé par conceptId avec colonnes FSN, PT FR, SAs, règles sélectionnées et erreurs.
    """
    check_result = check_result.loc[check_result["active"]=="1"]
    check_result["selected_rules"] = check_result.apply(combine_rule_selections, axis="columns")
    check_result["errors"] = check_result.apply(combine_rule_errors, axis="columns")
    check_result_agg_sctid = (
        check_result[['conceptId', 'selected_rules', 'errors', 'FSN', "PT_EN"]]
        .groupby("conceptId")
        .aggregate(
            fsn=pd.NamedAgg(column="FSN", aggfunc="first"),
            pt_en=pd.NamedAgg(column="PT_EN", aggfunc="first"),
            selected_rules=pd.NamedAgg(column="selected_rules", aggfunc=aggregate_combined),
            errors=pd.NamedAgg(column="errors", aggfunc=aggregate_combined)
        )
    )

    check_result_agg_sctid
    check_result_agg_sctid["pt_fr"] = (
        check_result
        .loc[check_result["acceptabilityId"]=="PREFERRED"]
        .set_index("conceptId")
        ["term"]
    )
    check_result_agg_sctid["nb_sa"] = (
        check_result[["conceptId", "term"]]
        .loc[check_result["acceptabilityId"]=="ACCEPTABLE"]
        .groupby("conceptId")
        .count()
    )
    for n in range(1, 11):
        check_result_agg_sctid[f"sa{n}"] = (
            check_result
            .loc[check_result["acceptabilityId"]=="ACCEPTABLE"]
            .groupby("conceptId")
            .nth(n-1)
            .set_index("conceptId")
            ["term"]
        )

    return check_result_agg_sctid
