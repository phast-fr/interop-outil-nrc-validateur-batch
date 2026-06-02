import logging
import pandas as pd

logger = logging.getLogger(__name__)

_GENERATORS: list = []


def rule_generator(fn):
    _GENERATORS.append(fn)
    return fn


@rule_generator
def generate_bs3_synonyms(preview: pd.DataFrame) -> pd.DataFrame:
    """Génère des synonymes selon la règle bs3 : 
    si FSN contient "structure", génère un synonyme "<pt_fr>, structure".

    args:
        preview: DataFrame des descriptions avant génération

    returns:
        DataFrame contenant uniquement les synonymes BS3 générés
    """

    bs3_synonyms = preview.loc[
        (
            preview["FSN_no_sem"].str.contains(
                r"structure", case=False, na=False
            )
            & (preview["active"] == "1")
            & (preview["acceptabilityId"] == "PREFERRED")
        )
    ].copy()
    bs3_synonyms["term"] = bs3_synonyms["term"] + ", structure"
    bs3_synonyms["id"] = bs3_synonyms["id"] + "_bs3"
    bs3_synonyms["active"] = "1"
    bs3_synonyms["_type_"] = "GENERATED"
    bs3_synonyms["acceptabilityId"] = "ACCEPTABLE"

    # éliminer les doublons avec les descriptions déjà présentes dans le preview
    bs3_synonyms = bs3_synonyms.loc[
        ~bs3_synonyms.apply(
            lambda row: (
                (preview["conceptId"] == row["conceptId"])
                & (preview["term"] == row["term"])
                & (preview["active"] == "1")
            ).any(),
            axis=1,
        )
    ]

    logger.info(
        f"Descriptions supplémentaires générées pour {len(bs3_synonyms)} lignes"
    )

    return bs3_synonyms


def generate_desc_from_rules(preview: pd.DataFrame) -> pd.DataFrame:
    """Génère des descriptions supplémentaires à partir de règles

    args:
        preview: DataFrame des descriptions

    returns:
        DataFrame contenant uniquement les descriptions supplémentaires
    """

    results = [gen(preview) for gen in _GENERATORS]
    return pd.concat(results, ignore_index=True)


def update_preview_with_generated(
    preview: pd.DataFrame, generated: pd.DataFrame
) -> pd.DataFrame:
    """Génère une nouvelle version du preview en intégrant les descriptions
    supplémentaires générées
    et en éliminant les lignes de type "VAL" en conséquence.

    args:
        preview: DataFrame des descriptions avant génération
        generated: DataFrame des descriptions générées

    returns:
        preview mis à jour avec les descriptions supplémentaires et sans les lignes de type "VAL" correspondantes
    """
    preview = pd.concat([preview, generated], ignore_index=True)
    preview = (
        preview
        .loc[
            ~(
                (preview["_type_"] == "VAL")
                & (preview["conceptId"].isin(generated["conceptId"]))
            )
        ]
    )

    return preview
