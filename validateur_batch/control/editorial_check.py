from typing import List

import regex
import re
import unicodedata
import pandas as pd


from validateur_batch.object import server


#####################
# Règles génériques #
#####################

def _check_case_significance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identifie les descriptions dont la casse du terme ne correspond pas à leur caseSignificanceId.

    args:
        df: DataFrame à valider

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions dont la casse du terme ne correspond pas à leur caseSignificanceId.
    """
    # Si tous les caractères du terme sont en minuscules, case significance devrait être "ci"
    mask_ci = (
        df.loc[:, "term"].str.islower() &
        (df.loc[:, "caseSignificanceId"] != "ci")
    )
    if mask_ci.any():
        df["case-ci"] = "0"
        df.loc[mask_ci, "case-ci"] = "1"

    mask_CS = (
        df.loc[:, "term"].str[0].str.isupper() &
        (df.loc[:, "caseSignificanceId"] != "CS")
    )
    if mask_CS.any():
        df["case-CS"] = "0"
        df.loc[mask_CS, "case-CS"] = "1"

    mask_cI = (
        ~df.loc[:, "term"].str[0].str.isupper() &
        ~df.loc[:, "term"].str.islower() & 
        (df.loc[:, "caseSignificanceId"] != "cI")
    )
    if mask_cI.any():
        df["case-cI"] = "0"
        df.loc[mask_cI, "case-cI"] = "1"

    return df

def _check_spaces(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identifie les descriptions contenant des caractères d'espace innatendus

    args:
        df: DataFrame à valider

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions contenant des caractères d'espace innatendus
    """
    NON_STANDARD_SPACE_RE = r"[\u00A0\u2000-\u200A\u202F\u205F\u3000\t\n\r\f\v]"

    # autres charactères d'espace
    mask_special = df["term"].str.contains(NON_STANDARD_SPACE_RE, regex=True)
    # doubles espaces
    mask_double = df["term"].str.contains(r"(?: {2,})", regex=True)
    # espace de début
    mask_head = df["term"].str.contains(r"^ ", regex=True)
    # espace de fin
    mask_trail = df["term"].str.contains(r"^ ", regex=True)

    mask_errors = mask_double | mask_head | mask_trail | mask_special
    if mask_errors.any():
        df["spaces"]="0"
        df.loc[mask_errors, "spaces"]="1"
    
    return df

def _check_chars(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identifie les descriptions contenant des caractères innatendus

    args:
        df: DataFrame à valider

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions contenant des caractères innatendus
    """

    AUTHORIZED_CHARS_RE = r"^[ \p{Script=Latin}0-9,():\x2d\-\x27\/\[\]+]*\Z"
    compiled = regex.compile(AUTHORIZED_CHARS_RE)
    def is_authorised(s):
        if compiled.match(s):
            return True
        else:
            return False
        
    mask_unauthorized = ~(df["term"].apply(is_authorised))

    if mask_unauthorized.any():
        df["char"]="0"
        df.loc[mask_unauthorized, "char"]="1"

    return df


def _check_unicity(df: pd.DataFrame, desc_act_fr: pd.DataFrame) -> pd.DataFrame:
    """Identifie les descriptions actives dupliquées

    args:
        df: DataFrame à valider
        desc_act_fr : descriptions actives de l'édition nationale fr

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant la règle d'unicité
    """
    df_active =  df.loc[df["active"]=="1"].copy()

    idx = df_active.loc[
        (df_active["term"].duplicated(keep=False))
    ].index
    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"duplicate": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")
        
    return df


def _check_ar2(df: pd.DataFrame) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle ar2.

    args:
        df: DataFrame à valider

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle ar2.
    """
    idx = df.loc[df.loc[:, "term"].str.contains("^(?:les?|la|une?) ", case=False)].index
    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"ar2": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df

def _check_ar4_FR(df: pd.DataFrame, bs: pd.DataFrame) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle ar4_FR.

    args:
        df: DataFrame à valider
        bs: Filtre sur les Body structure de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle ar4_FR.
    """
    idx_base = df.loc[bs &
                 ~df.loc[:, "FSN_no_sem"].str.contains(r"(?:single)\b", case=False)
                 & df.loc[:, "term"].str.contains(r"(?:d'une?\b)", case=False)].index
    if not idx_base.empty:
        df = pd.merge(df, pd.DataFrame(data={"ar4_FR_base": ["1"] * len(idx_base)}, index=idx_base),
                      how="left", left_index=True, right_index=True, validate="1:1")

    idx_single = df.loc[bs &
                    df.loc[:, "FSN_no_sem"].str.contains(r"single\b", case=False)
                    & ~df.loc[:, "term"].str.contains(r"(?:d'une?\b)", case=False)].index

    if not idx_single.empty:
        df = pd.merge(df, pd.DataFrame(data={"ar4_FR_single": ["1"] * len(idx_single)}, index=idx_single),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_ar6(df: pd.DataFrame, sb: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle ar6.

    args:
        df: DataFrame à valider
        sb: Filtre sur les Physical object de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle ar6.
    """
    idx = df.loc[sb
                 & (df.loc[:, "term"].str.contains(" (?:les?|la|une?|d'une?) ", case=False))].index # noqa
    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"ar6": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_ll1(df: pd.DataFrame) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle ll1.

    args:
        df: DataFrame à valider

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle ll1.
    """
    mask_oe = df["term"].str.contains(r"[oO][eE]", regex=True)
    mask_ae = df["term"].str.contains(r"[aA][eE]", regex=True)
    mask_error = mask_oe | mask_ae
    if mask_error.any():
        df["ll1"] = "0"
        df.loc[mask_error, "ll1"] = "1"

    return df

def _check_or4(df: pd.DataFrame) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle or4.

    args:
        df: DataFrame à valider

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle or4.
    """
    mask = {}
    mask_error = pd.Series([False]*len(df), df.index)
    PREFIXES = ["demi", "mi", "semi", "ex", "sous", "vice", "non"]
    EXCEPTIONS = ["extern", "extrém", "extrem", "excré", "mineur", "micro", "mini", "mitral", "extra", "except"]
    for prefix in PREFIXES:
        mask[prefix] = (
            df["term"].str.contains(rf"\b{prefix}[^\-]", regex=True) &
            ~df["term"].str.contains(rf"\b(?:{'|'.join(EXCEPTIONS)})", regex=True)
        )
        mask_error = mask_error | mask[prefix]
    
    if mask_error.any():
        df["or4"] = "0"
        df.loc[mask_error, "or4"] = "1"

    return df

def _check_se4(df: pd.DataFrame) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle se4

    args:
        df: DataFrame à valider

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle se4
    """
    REGEX_UNIT_ATOM = r"(?:[numk]?(?:g|mol|L|m))"
    REGEX_FORBIDDEN_SLASH = r'(?!\b(?:'+ REGEX_UNIT_ATOM + r'|et|[0-9]))/(?!(?:' + REGEX_UNIT_ATOM + r'|ou|[0-9])\b)'
    print(REGEX_FORBIDDEN_SLASH)
    mask_error = df["term"].str.contains(REGEX_FORBIDDEN_SLASH, regex=True)
    
    if mask_error.any():
        df["se4"] = "0"
        df.loc[mask_error, "se4"] = "1"

    return df

#########################
# Règles Body structure #
#########################
def _check_bs2(df: pd.DataFrame,  pt: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle bs2.

    args:
        df: DataFrame à valider
        pt: Filtre sur les termes préférés de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle bs2.
    """
    idx = df.loc[pt & (df.loc[:, "FSN_no_sem"].str.contains("joint", regex=False, case=False))
                 & (~df.loc[:, "term"].str.contains("(?:articulation|articulaire)", case=False))].index # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"bs2": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")
    return df


def _check_bs3(df: pd.DataFrame, bs: pd.Series, pt: pd.Series, syn: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle bs3
    args:
        df: DataFrame à valider
        bs: Filtre sur les Body structure de `df`
        pt: Filtre sur les termes préférés de `df`
        syn: Filtre sur les synonymes acceptables de `df`
    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle bs3
    """

    REGEX_ADJECTIVAL = r"(?:(?:\S*aires?)|(?:\S*ienn?e?s?)|(?:\S*iques?)|(?:\S*ales?)|(?:\S*eux)|(?:\S*euses?)|(?:\S*ales?)|(?:\S*elles?)|\S*ine?s?|(?:\S*ois(?:es)?))" # noqa

    idx = df.loc[bs & pt
                 & (df.loc[:, "FSN_no_sem"].str.contains("structure", regex=False, case=False))
                 & (df.loc[:, "term"].str.contains(f"structure(?!s? {REGEX_ADJECTIVAL})", regex=True, case=False))].index # noqa
    
    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"bs3-struct": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    # éviter structure et entier dans le même
    idx = df.loc[bs
                 & (df.loc[:, "term"].str.contains(f"structure.*enti[eè]", regex=True, case=False))].index # noqa
    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"bs3-struct-ent": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    idx = df.loc[bs & pt
                & (df.loc[:, "FSN_no_sem"].str.contains(r"\bentire\b", regex=True, case=False)) # noqa
                & (~df.loc[:, "term"].str.contains("(?:entiers?|entières?)", case=False))].index # noqa
    
    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"bs3-entire": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    idx = df.loc[bs & pt
                & (df.loc[:, "FSN_no_sem"].str.contains(r"\bpart\b", regex=True, case=False)) # noqa
                & (~df.loc[:, "term"].str.contains("partie", regex=False, case=False))].index

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"bs3-part": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")
    return df

def _remove_accents(s):
    """Supprime les diacritiques d'une chaîne de caractères.

    args:
        s: Chaîne à traiter

    returns:
        Chaîne sans diacritiques, ou chaîne vide si `s` n'est pas une str.
    """
    if not isinstance(s, str):
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )


def _pattern_from_terminology_anatomica(nomenclature: List[str]) -> str:
    """Construit un pattern regex à partir de la terminologie anatomique.
    Soit la liste des anciens termes, soit la liste des nouveaux termes

    args:
        nomenclature: Liste des termes de la terminologie anatomique

    returns:
        Pattern regex pour identifier les termes de la terminologie anatomique
    """
    entre_par = re.compile(r'\(.*\)')

    lower_unaccented_nomenclature = [
        str.lower(entre_par.sub('',_remove_accents(t)))
        for t in nomenclature
    ]
    lower_unaccented_nomenclature = [
        str.strip(part)
        for item in lower_unaccented_nomenclature
        for part in item.split("/")
        if part  # garde uniquement les non vides
    ]

    pattern_list = [f"(?:{s})" for s in lower_unaccented_nomenclature]
    pattern = "|".join(pattern_list)
    return pattern


def _check_bs4(
    df: pd.DataFrame, anats: pd.Series, terminology_anatomica: pd.DataFrame, pt: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle bs4
    args:
        df: DataFrame à valider
        anats : Filtre sur les termes descendants de anatomical structure
        terminology_anatomica: DataFrame contenant la terminologie anatomique
        pt: Filtre sur les termes préférés de `df`
    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle bs4.
    """
 
    pattern_old = _pattern_from_terminology_anatomica(terminology_anatomica["Ancienne nomenclature"])
    pattern_new = _pattern_from_terminology_anatomica(terminology_anatomica["Nouvelle nomenclature"])

    df_check_ta = df.copy()
    df_check_ta["term_no_accents"] = df_check_ta["term"].apply(_remove_accents)

    mask_ta = (
        pt 
        & anats 
        & df_check_ta["term_no_accents"].str.contains(pattern_old, case=False, na=False)
        & ~df_check_ta["term_no_accents"].str.contains(pattern_new, case=False, na=False)
    )

    filtered_df = df_check_ta[mask_ta].copy()

    idx = filtered_df.index

    if not idx.empty:
        df = pd.merge(
            df,
            pd.DataFrame(data={"bs4": ["1"] * len(idx)}, index=idx),
            how="left",
            left_index=True,
            right_index=True,
            validate="1:1",
        )

    return df

def _check_bs5(df: pd.DataFrame, bs: pd.Series, pt: pd.Series, syn: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle bs5
    args:
        df: DataFrame à valider
        bs: Filtre sur les Body structure de `df`
        pt: Filtre sur les termes préférés de `df`
        syn: Filtre sur les synonymes acceptables de `df`
    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle bs5.
    """
    idx = df.loc[pt & bs
                 & (df.loc[:, "FSN"].str.contains("region", regex=False, case=False))
                 & (~df.loc[:, "term"].str.contains("région", regex=False, case=False))].index # noqa
    
    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"bs5": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")
    return df


def _check_bs6(df: pd.DataFrame, bs: pd.Series, bsr: pd.Series, pt: pd.Series, syn: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle bs6
    args:
        df: DataFrame à valider
        bs: Filtre sur les Body structure de `df`
        bsr: Filtre sur les Body structure root de `df`
        pt: Filtre sur les termes préférés de `df`
        syn: Filtre sur les synonymes acceptables de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle bs6.
    """

    idx = df.loc[bs
                 & (df.loc[:, "FSN_no_sem"].str.contains("zone", regex=False, case=False))
                 & (~df.loc[:, "term"].str.contains("zone", regex=False, case=False))].index # noqa

    idx = idx.union(df.loc[bs & bsr
                           & (df.loc[:, "FSN_no_sem"].str.contains(r"\barea\b", regex=True, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains(r"\b(?:zone|surface|aire)\b", case=False))].index) # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"bs6": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")
    return df


def _check_bs7(df: pd.DataFrame, bs: pd.Series, pt: pd.Series, syn: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle bs7

    args:
        df: DataFrame à valider
        bs: Filtre sur les Body structure de `df`
        pt: Filtre sur les termes préférés de `df`
        syn: Filtre sur les synonymes acceptables de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle bs7.
    """
    idx = df.loc[pt & bs
                 & (df.loc[:, "FSN_no_sem"].str.contains(r"\bproper\b", regex=True, case=False))
                 & (~df.loc[:, "term"].str.contains(r"(?:propre|proprement dite?)", case=False))].index # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"bs7": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_bs8(df: pd.DataFrame, pt: pd.Series, syn: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle bs8

    args:
        df: DataFrame à valider
        pt: Filtre sur les termes préférés de `df`
        syn: Filtre sur les synonymes acceptables de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle bs8.
    """
    idx = df.loc[pt
                 & (df.loc[:, "FSN_no_sem"].str.contains("apex", regex=False, case=False))
                 & (~df.loc[:, "term"].str.contains("apex", regex=False, case=False))].index # noqa

    idx = idx.union(df.loc[syn
                           & (df.loc[:, "FSN_no_sem"].str.contains(r"\bapex\b", regex=True, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains(r"(?:apex|pointe|bout|cime)", case=False))].index) # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"bs8": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_bs9(df: pd.DataFrame, pt: pd.Series, syn: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle bs9.

    args:
        df: DataFrame à valider
        pt: Filtre sur les termes préférés de `df`
        syn: Filtre sur les synonymes acceptables de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle bs9.
    """
    idx = df.loc[pt
                 & (df.loc[:, "FSN_no_sem"].str.contains("lesser toe", regex=False, case=False)) # noqa
                 & (~df.loc[:, "term"].str.contains("orteil excepté l'hallux", regex=False, case=False))].index # noqa

    idx = idx.union(df.loc[syn
                           & (df.loc[:, "FSN_no_sem"].str.contains("lesser toe", regex=False, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("(?:orteil latéral|orteil excepté l'hallux)", case=False))].index) # noqa

    idx = idx.union(df.loc[(df.loc[:, "FSN_no_sem"].str.contains("lesser toe", regex=False, case=False)) # noqa
                           & (df.loc[:, "term"].str.contains("petit orteil", case=False))].index) # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"bs9": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_bs10(df: pd.DataFrame, pt: pd.Series, syn: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle bs10-FR

    args:
        df: DataFrame à valider
        pt: Filtre sur les termes préférés de `df`
        syn: Filtre sur les synonymes acceptables de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle bs10.
    """
    # bs10 / lower limb
    idx_lower_limb_pt = df.loc[pt & 
                 (df.loc[:, "FSN"].str.contains("lower limb", regex=False, case=False))
                 & (~df.loc[:, "term"].str.contains("membre inférieur", regex=False, case=False))].index # noqa

    idx_lower_limb_syn = df.loc[syn & 
                 (df.loc[:, "FSN"].str.contains("lower limb", regex=False, case=False))
                 & (~df.loc[:, "term"].str.contains(r"\b(?:membre(?: (?:droit|gauche)) inférieur|membrum inferius|membri inferioris)\b", regex=True, case=False))].index # noqa

    idx_lower_limb = idx_lower_limb_pt.union(idx_lower_limb_syn)
    if not idx_lower_limb.empty:
        df = pd.merge(df, pd.DataFrame(data={"bs10-limb": ["1"] * len(idx_lower_limb)}, index=idx_lower_limb),
                      how="left", left_index=True, right_index=True, validate="1:1")

    # bs10 / lower leg erreur dans la traduction
    idx_pt_lower_leg_not_ok = df.loc[pt
                           & (df.loc[:, "FSN"].str.contains("lower leg", regex=False, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains(r"partie inférieure(?: (?:entière|gauche|droite))* de la jambe", case=False))].index  # noqa

    idx_syn_lower_leg_not_ok = df.loc[
        syn
        & (
            df.loc[:, "FSN_no_sem"].str.contains(
                "lower leg", regex=False, case=False
            )
        )  # noqa
        & (
            ~df.loc[:, "term"].str.contains(
                r"(partie inférieure( (entière|gauche|droite))* de la jambe)|"
                + r"(partie basse( (entière|gauche|droite))* de la jambe)|"
                + r"(jambe( (entière|gauche|droite))*, du genou à la cheville)",
                case=False,
            ) # noqa
        )
    ].index

    idx_lower_leg = idx_pt_lower_leg_not_ok.union(idx_syn_lower_leg_not_ok)

    if not idx_lower_leg.empty:
        df = pd.merge(df, pd.DataFrame(data={"bs10-lower-leg": ["1"] * len(idx_lower_leg)}, index=idx_lower_leg),
                      how="left", left_index=True, right_index=True, validate="1:1")

    # bs10 / missing syn        
    df_pt_lower_leg = df.loc[pt & (df.loc[:, "FSN_no_sem"].str.contains("lower leg", regex=False, case=False))]
    
    df_syn_lower_leg_ok = df.loc[syn    
                           & (df.loc[:, "FSN_no_sem"].str.contains("lower leg", regex=False, case=False)) # noqa
                           & (df.loc[:, "term"].str.contains(r"(?:partie basse( (entière|gauche|droite))* de la jambe)", case=False))] 
    
    df_pt_syn_lower_leg = df_pt_lower_leg.merge(df_syn_lower_leg_ok, how = "left", on="conceptId"  )

    df_pt_syn_lower_leg_no_match = df_pt_syn_lower_leg.loc[df_pt_syn_lower_leg["FSN_y"].isna()] #y
    idx_df_pt_syn_lower_leg_no_match = df[df["FSN"].isin(df_pt_syn_lower_leg_no_match["FSN_x"].values)].index #x

    if not idx_df_pt_syn_lower_leg_no_match.empty:
        df = pd.merge(df, pd.DataFrame(data={"bs10-miss": ["1"] * len(idx_df_pt_syn_lower_leg_no_match)}, index=idx_df_pt_syn_lower_leg_no_match),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_bs11(df: pd.DataFrame, pt: pd.Series, syn: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle bs11-FR

    args:
        df: DataFrame à valider
        pt: Filtre sur les termes préférés de `df`
        syn: Filtre sur les synonymes acceptables de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle bs11-FR.
    """
    # bs11 / upper limb
    idx_limb_pt = df.loc[pt &
                 (df.loc[:, "FSN_no_sem"].str.contains("upper limb", regex=False, case=False))
                 & (~df.loc[:, "term"].str.contains("membre supérieur", regex=False, case=False))].index # noqa

    idx_limb_syn = df.loc[syn &
                 (df.loc[:, "FSN_no_sem"].str.contains("upper limb", regex=False, case=False))
                 & (~df.loc[:, "term"].str.contains(r"\b(?:membre supérieur|membrum superius|membri superioris)\b", regex=True, case=False))].index # noqa  

    idx_limb = idx_limb_pt.union(idx_limb_syn)
    if not idx_limb.empty:
        df = pd.merge(df, pd.DataFrame(data={"bs11-limb": ["1"] * len(idx_limb)}, index=idx_limb),
                      how="left", left_index=True, right_index=True, validate="1:1")    

    # bs11 / upper arm : traduction incorrecte
    idx_pt_upper_arm_not_ok = df.loc[pt
                           & (df.loc[:, "FSN_no_sem"].str.contains("upper arm", regex=False, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains(r"partie supérieure(?: (?:entière|gauche|droite))* du bras", case=False))].index  # noqa

    idx_syn_upper_arm_not_ok = df.loc[
        syn
        & (
            df.loc[:, "FSN_no_sem"].str.contains(
                "upper arm", regex=False, case=False
            )
        )  # noqa
        & (
            ~df.loc[:, "term"].str.contains(
                r"(bras( (entier|droit|gauche))*, de l'épaule au coude)|"+
                r"(partie supérieure( (entière|gauche|droite))* du bras)",
                case=False,
            )
        )
    ].index

    idx_upper_arm = idx_pt_upper_arm_not_ok.union(idx_syn_upper_arm_not_ok)

    if not idx_upper_arm.empty:
        df = pd.merge(df, pd.DataFrame(data={"bs11-upper-arm": ["1"] * len(idx_upper_arm)}, index=idx_upper_arm),
                      how="left", left_index=True, right_index=True, validate="1:1")
        
    # bs11 / upper arm : synonyme manquant
    df_pt_upper_arm = df.loc[pt & (df.loc[:, "FSN_no_sem"].str.contains("upper arm", regex=False, case=False))]
    
    df_syn_upper_arm_ok = df.loc[syn    
                           & (df.loc[:, "FSN_no_sem"].str.contains("upper arm", regex=False, case=False)) # noqa
                           & (df.loc[:, "term"].str.contains(r"(bras( (entier|droit|gauche))*, de l'épaule au coude)", case=False))] 
    
    df_pt_syn_upper_arm = df_pt_upper_arm.merge(df_syn_upper_arm_ok, how = "left", on="conceptId")

    df_pt_syn_upper_arm_no_match = df_pt_syn_upper_arm.loc[df_pt_syn_upper_arm["FSN_y"].isna()] #y
    idx_df_pt_syn_upper_arm_no_match = df[df["FSN"].isin(df_pt_syn_upper_arm_no_match["FSN_x"].values)].index #x

    if not idx_df_pt_syn_upper_arm_no_match.empty:
        df = pd.merge(df, pd.DataFrame(data={"bs11-miss": ["1"] * len(idx_df_pt_syn_upper_arm_no_match)}, index=idx_df_pt_syn_upper_arm_no_match),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_bs12(df: pd.DataFrame, pt: pd.Series, syn: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle bs12
    args:
        df: DataFrame à valider
        pt: Filtre sur les termes préférés de `df`
        syn: Filtre sur les synonymes acceptables de `df`
    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle bs12.
    """
    idx = df.loc[pt &
                 (df.loc[:, "FSN_no_sem"].str.contains("cerebrum", regex=False, case=False))
                 & (~df.loc[:, "term"].str.contains("cerveau", regex=False, case=False))].index # noqa
    
    idx = df.loc[syn &
                 (df.loc[:, "FSN_no_sem"].str.contains("cerebrum", regex=False, case=False))
                 & (~df.loc[:, "term"].str.contains(r"(?:cerveau)|(?:télencéphale)", regex=True, case=False))].index # noqa
    
    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"bs12": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")
    return df


def _check_bs13(df: pd.DataFrame) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle bs13

    args:
        df: DataFrame à valider

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle bs13.
    """
    idx = df.loc[(df.loc[:, "FSN_no_sem"].str.contains("brain", regex=False, case=False))
                 & (~df.loc[:, "term"].str.contains("encéphale", regex=False, case=False))].index # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"bs13": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


###########################
# Règles Clinical finding #
###########################
def _check_co2(df: pd.DataFrame, co: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle co2

    args:
        df: DataFrame à valider
        co: Filtre sur les Clinical finding de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle co2.
    """
    idx = df.loc[co
                 & (df.loc[:, "FSN_no_sem"].str.contains(r"(?<!\()finding(?!\))", case=False))
                 & (~df.loc[:, "term"].str.contains("constatation", regex=False, case=False))].index # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"co2": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_co6(df: pd.DataFrame, co: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle co6-FR

    args:
        df: DataFrame à valider
        co: Filtre sur les Clinical finding de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle co6-FR.
    """
    idx = df.loc[co
                 & (df.loc[:, "FSN_no_sem"].str.contains("above reference range", regex=False, case=False)) # noqa
                 & (~df.loc[:, "term"].str.contains("supérieure? (?:à l'intervalle|aux valeurs) de référence", case=False))].index # noqa

    idx = idx.union(df.loc[co
                           & (df.loc[:, "FSN_no_sem"].str.contains("below reference range", regex=False, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("inférieure? (?:à l'intervalle|aux valeurs) de référence", case=False))].index) # noqa

    idx = idx.union(df.loc[co
                           & (df.loc[:, "FSN_no_sem"].str.contains("within reference range", regex=False, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("dans (?:l'intervalle|les valeurs) de référence", case=False))].index) # noqa

    idx = idx.union(df.loc[co
                           & (df.loc[:, "FSN_no_sem"].str.contains("outside reference range", regex=False, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("en dehors (?:de l'intervalle|des valeurs) de référence", case=False))].index) # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"co6": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_pa3_1(df: pd.DataFrame) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle pa3.1

    args:
        df: DataFrame à valider

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle pa3.1.
    """
    idx = df.loc[(df.loc[:, "FSN_no_sem"].str.contains("pressure injury", regex=False, case=False)) # noqa
                 & (~df.loc[:, "term"].str.contains("escarre", regex=False, case=False))].index # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"pa3.1": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_pa4(df: pd.DataFrame) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle pa4

    args:
        df: DataFrame à valider

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle pa4.
    """
    idx = df.loc[(df.loc[:, "FSN_no_sem"].str.contains("epilepsy", regex=False, case=False))
                 & (~df.loc[:, "term"].str.contains("épilepsie", regex=False, case=False))].index # noqa

    idx = idx.union(df.loc[(df.loc[:, "FSN_no_sem"].str.contains("seizure", regex=False, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("(?:crise|convulsion|convulsif|convulsive)", case=False))].index) # noqa

    idx = idx.union(df.loc[(df.loc[:, "FSN_no_sem"].str.contains("convulsion", regex=False, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("convulsion", regex=False, case=False))].index) # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"pa4": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_pa6(df: pd.DataFrame) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle pa6

    args:
        df: DataFrame à valider

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle pa6.
    """
    idx = df.loc[(df.loc[:, "FSN_no_sem"].str.contains("impairment", regex=False, case=False))
                 & (~df.loc[:, "term"].str.contains("atteinte", regex=False, case=False))].index # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"pa6": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_pa7(df: pd.DataFrame) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle pa7

    args:
        df: DataFrame à valider

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle pa7.
    """
    idx = df.loc[(df.loc[:, "FSN_no_sem"].str.contains("primary", regex=False, case=False))
                 & (~df.loc[:, "term"].str.contains("(?:primitif|primitive|primaire)", case=False))].index # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"pa7": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_pa8(df: pd.DataFrame) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle pa8

    args:
        df: DataFrame à valider

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle pa8.
    """
    idx = df.loc[(df.loc[:, "FSN_no_sem"].str.contains("chilblain", regex=False, case=False))
                 & (~df.loc[:, "term"].str.contains("engelure", regex=False, case=False))].index # noqa

    idx = idx.union(df.loc[(df.loc[:, "FSN_no_sem"].str.contains("(?<!superficial )frostbite", case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("(?:^| )gelure", case=False))].index) # noqa

    idx = idx.union(df.loc[(df.loc[:, "FSN_no_sem"].str.contains("superficial frostbite", regex=False, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("(?:^| )gelure superficielle", case=False))].index) # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"pa8": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_pa9(df: pd.DataFrame) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle pa9

    args:
        df: DataFrame à valider

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle pa9.
    """
    idx = df.loc[(df.loc[:, "FSN_no_sem"].str.contains("carbuncle", regex=False, case=False))
                 & (~df.loc[:, "term"].str.contains("anthrax", regex=False, case=False))].index # noqa

    idx = idx.union(df.loc[(df.loc[:, "FSN_no_sem"].str.contains("(?:furuncle|boil)", case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("(?:furoncle|folliculite nécrotique|clou)", case=False))].index) # noqa

    idx = idx.union(df.loc[(df.loc[:, "FSN_no_sem"].str.contains("anthrax", regex=False, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("maladie du charbon", regex=False, case=False))].index) # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"pa9": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


##############################################
# Règles Pharmaceutical / biological product #
##############################################
def _check_me1(df: pd.DataFrame, me: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle me1

    args:
        df: DataFrame à valider
        me: Filtre sur les Pharmaceutical / biological product de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle me1.
    """
    idx = df.loc[me
                 & (df.loc[:, "FSN_no_sem"].str.contains("product containing (?!only|precisely)", case=False)) # noqa
                 & (~df.loc[:, "term"].str.contains("produit contenant (?!uniquement|précisément)", case=False))].index # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"me1": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")
    return df


def _check_me2(df: pd.DataFrame, me: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle me2

    args:
        df: DataFrame à valider
        me: Filtre sur les Pharmaceutical / biological product de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle me2.
    """
    idx = df.loc[me
                 & (df.loc[:, "FSN_no_sem"].str.contains("product containing only", regex=False, case=False)) # noqa
                 & (~df.loc[:, "term"].str.contains("produit contenant uniquement", regex=False, case=False))].index # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"me2": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_me3(df: pd.DataFrame, me: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle me3

    args:
        df: DataFrame à valider
        me: Filtre sur les Pharmaceutical / biological product de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle me3.
    """
    idx = df.loc[me
                 & (df.loc[:, "FSN_no_sem"].str.endswith("(clinical drug)"))
                 & (~df.loc[:, "term"].str.contains("produit contenant précisément", regex=False, case=False))].index # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"me3": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_me4(df: pd.DataFrame, me: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle me4

    args:
        df: DataFrame à valider
        me: Filtre sur les Pharmaceutical / biological product de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle me4.
    """
    idx = df.loc[me
                 & (df.loc[:, "term"].str.contains("libération conventionnelle", regex=False, case=False))].index # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"me4": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


##########################
# Règles Physical object #
##########################
def _check_sb1(df: pd.DataFrame) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle sb1

    args:
        df: DataFrame à valider

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle sb1.
    """
    idx = df.loc[(df.loc[:, "FSN_no_sem"].str.contains(r"evacuated [-\w\s\/\(\)':]+ collection tube", case=False)) # noqa
                 & (~df.loc[:, "term"].str.contains(r"tube sous vide [-\w\s\/\(\)':]+ pour prélèvement", case=False))].index # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"sb1": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_sb2(df: pd.DataFrame) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle sb2

    args:
        df: DataFrame à valider

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle sb2.
    """
    idx = df.loc[(df.loc[:, "FSN_no_sem"].str.contains(r"evacuated [-\w\s\/\(\)':]+ specimen container", case=False)) # noqa
                 & (~df.loc[:, "term"].str.contains(r"support sous vide [-\w\s\/\(\)':]+ pour prélèvement", case=False))].index # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"sb2": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_sb3(df: pd.DataFrame, pt: pd.Series, syn: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle sb3

    args:
        df: DataFrame à valider
        pt: Filtre sur les termes préférés de `df`
        syn: Filtre sur les synonymes acceptables de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle sb3.
    """
    idx = df.loc[pt
                 & (df.loc[:, "FSN_no_sem"].str.contains("stent", regex=False, case=False))
                 & (~df.loc[:, "term"].str.contains("endoprothèse", regex=False, case=False))].index # noqa

    idx = idx.union(df.loc[syn
                           & (df.loc[:, "FSN_no_sem"].str.contains("stent", regex=False, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("stent", regex=False, case=False))].index) # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"sb3": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


####################
# Règles Procedure #
####################
def _check_pr2(df: pd.DataFrame, pt: pd.Series, syn: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle pr2

    args:
        df: DataFrame à valider
        pt: Filtre sur les termes préférés de `df`
        syn: Filtre sur les synonymes acceptables de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle pr2.
    """
    idx = df.loc[pt
                 & (df.loc[:, "FSN_no_sem"].str.contains(" procedure", regex=False, case=False)) # noqa
                 & (~df.loc[:, "term"].str.contains("(?:procédure|intervention chirurgicale)", case=False))].index # noqa

    idx = idx.union(df.loc[pt
                           & (df.loc[:, "FSN_no_sem"].str.contains("operation", regex=False, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("intervention chirurgicale", regex=False, case=False))].index) # noqa

    idx = idx.union(df.loc[syn
                           & (df.loc[:, "FSN_no_sem"].str.contains(" procedure", regex=False, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("(?:intervention|opération|chirurgie)", case=False))].index) # noqa

    idx = idx.union(df.loc[syn
                           & (df.loc[:, "FSN_no_sem"].str.contains("operation", regex=False, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("(?:opération|chirurgie)", case=False))].index) # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"pr2": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_pr3(df: pd.DataFrame) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle pr3

    args:
        df: DataFrame à valider

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle pr3.
    """
    idx = df.loc[(df.loc[:, "FSN_no_sem"].str.contains("consultation", regex=False, case=False)) # noqa
                 & (~df.loc[:, "term"].str.contains("consultation", regex=False, case=False))].index # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"pr3": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_pr4(df: pd.DataFrame, pt: pd.Series, syn: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle pr4

    args:
        df: DataFrame à valider
        pt: Filtre sur les termes préférés de `df`
        syn: Filtre sur les synonymes acceptables de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle pr4.
    """
    idx = df.loc[(df.loc[:, "FSN_no_sem"].str.contains("removal of foreign body", regex=False, case=False)) # noqa
                 & (~df.loc[:, "term"].str.contains("retrait d'un corps étranger", regex=False, case=False))].index # noqa

    idx = idx.union(df.loc[pt
                           & (df.loc[:, "FSN_no_sem"].str.contains("magnet extraction", regex=False, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("extraction avec un aimant", regex=False, case=False))].index) # noqa

    idx = idx.union(df.loc[syn
                           & (df.loc[:, "FSN_no_sem"].str.contains("magnet extraction", regex=False, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains(r"retrait d'un corps étranger [-\w\s\/\(\)':]+ à l'aide d'un aimant", case=False))].index) # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"pr4": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_pr9(df: pd.DataFrame, pt: pd.Series, syn: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle pr9

    args:
        df: DataFrame à valider
        pt: Filtre sur les termes préférés de `df`
        syn: Filtre sur les synonymes acceptables de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle pr9.
    """
    idx = df.loc[pt
                 & (df.loc[:, "FSN_no_sem"].str.contains("excisional biopsy", regex=False, case=False)) # noqa
                 & (~df.loc[:, "term"].str.contains("biopsie-exérèse", regex=False, case=False))].index # noqa

    idx = idx.union(df.loc[syn
                           & (df.loc[:, "FSN_no_sem"].str.contains("excisional biopsy", regex=False, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("biopsie excisionnelle", regex=False, case=False))].index) # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"pr9": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_pr10(df: pd.DataFrame) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle pr10

    args:
        df: DataFrame à valider

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle pr10.
    """
    idx = df.loc[(df.loc[:, "FSN_no_sem"].str.contains("incisional biopsy", regex=False, case=False)) # noqa
                 & (~df.loc[:, "term"].str.contains("biopsie incisionnelle", regex=False, case=False))].index # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"pr10": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_pr12(df: pd.DataFrame, pt: pd.Series, syn: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle pr12

    args:
        df: DataFrame à valider
        pt: Filtre sur les termes préférés de `df`
        syn: Filtre sur les synonymes acceptables de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle pr12.
    """
    idx = df.loc[pt
                 & (df.loc[:, "FSN_no_sem"].str.contains("MRI", regex=False))
                 & (~df.loc[:, "term"].str.contains("IRM", regex=False, case=False))].index # noqa

    idx = idx.union(df.loc[syn
                           & (df.loc[:, "FSN_no_sem"].str.contains("MRI", regex=False))
                           & (~df.loc[:, "term"].str.contains("imagerie par résonance magnétique", regex=False, case=False))].index) # noqa

    idx = idx.union(df.loc[pt
                           & (df.loc[:, "FSN_no_sem"].str.contains("magnetic resonance angiography", regex=False, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("angiographie par IRM", regex=False, case=False))].index) # noqa

    idx = idx.union(df.loc[syn
                           & (df.loc[:, "FSN_no_sem"].str.contains("magnetic resonance angiography", regex=False, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("angiographie par imagerie par résonance magnétique", regex=False, case=False))].index) # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"pr12": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_pr13(df: pd.DataFrame, pt: pd.Series, syn: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle pr13

    args:
        df: DataFrame à valider
        pt: Filtre sur les termes préférés de `df`
        syn: Filtre sur les synonymes acceptables de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle pr13.
    """
    idx = df.loc[pt
                 & (df.loc[:, "FSN_no_sem"].str.contains("(?:guided|guidance)", case=False))
                 & (~df.loc[:, "term"].str.contains("guidée? par", case=False))].index

    idx = idx.union(df.loc[syn
                           & (df.loc[:, "FSN_no_sem"].str.contains("(?:guided|guidance)", case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("sous guidage", regex=False, case=False))].index) # noqa

    idx = idx.difference(df.loc[df.loc[:, "FSN_no_sem"].str.contains("(?:fluoroscopy|fluoroscopic)", case=False)].index) # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"pr13": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_pr14(df: pd.DataFrame, pt: pd.Series, syn: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle pr14

    args:
        df: DataFrame à valider
        pt: Filtre sur les termes préférés de `df`
        syn: Filtre sur les synonymes acceptables de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle pr14.
    """
    idx = df.loc[pt
                 & (df.loc[:, "FSN_no_sem"].str.contains(r"(?:fluoroscopy|fluoroscopic)(?![-\w\s\/\(\)':]*(?:guided|guidance))", case=False)) # noqa
                 & (~df.loc[:, "term"].str.contains("radioscopie", case=False))].index

    idx = idx.union(df.loc[syn
                           & (df.loc[:, "FSN_no_sem"].str.contains(r"(?:fluoroscopy|fluoroscopic)(?![-\w\s\/\(\)':]*(?:guided|guidance))", case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("fluoroscopie", regex=False, case=False))].index) # noqa

    idx = idx.union(df.loc[pt
                           & (df.loc[:, "FSN_no_sem"].str.contains(r"(?:fluoroscopy|fluoroscopic)[-\w\s\/\(\)':]*(?:guided|guidance)", case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("guidée? par radioscopie", case=False))].index) # noqa

    idx = idx.union(df.loc[syn
                           & (df.loc[:, "FSN_no_sem"].str.contains(r"(?:fluoroscopy|fluoroscopic)[-\w\s\/\(\)':]*(?:guided|guidance)", case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("(?:sous guidage radioscopique|guidée? par fluoroscopie)", case=False))].index) # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"pr14": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_pr15(df: pd.DataFrame, pr: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle pr15-FR

    Args:
        df: DataFrame à valider
        pr: Filtre sur les Procedure de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle pr15-FR.
    """
    idx = df.loc[pr
                 & (df.loc[:, "FSN_no_sem"].str.contains("education", regex=False, case=False))
                 & (~df.loc[:, "term"].str.contains("éducation", case=False))].index

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"pr15": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


##########################################
# Règles Situation with explicit context #
##########################################
def _check_hs1(df: pd.DataFrame, hs: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle hs1

    args:
        df: DataFrame à valider
        hs: Filtre sur les Situation with explicit context de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle hs1.
    """
    idx = df.loc[hs
                 & (df.loc[:, "FSN_no_sem"].str.contains("history", regex=False, case=False))
                 & (~df.loc[:, "term"].str.contains("antécédent(?!s)", case=False))].index # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"hs1": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


###################
# Règles Specimen #
###################
def _check_ec2(df: pd.DataFrame) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle ec2

    args:
        df: DataFrame à valider

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle ec2.
    """
    idx = df.loc[(df.loc[:, "FSN_no_sem"].str.contains("submitted as specimen", regex=False, case=False)) # noqa
                 & (~df.loc[:, "term"].str.contains("présentée? comme échantillon", case=False))].index # noqa

    idx = idx.union(df.loc[(df.loc[:, "FSN_no_sem"].str.contains("washings", regex=False, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("liquide de lavage", regex=False, case=False))].index) # noqa

    idx = idx.union(df.loc[(df.loc[:, "FSN_no_sem"].str.contains("cytologic material", regex=False, case=False)) # noqa
                           & (~df.loc[:, "term"].str.contains("matériel cytologique", regex=False, case=False))].index) # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"ec2": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_ec4(df: pd.DataFrame) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle ec4

    args:
        df: DataFrame à valider

    returns:
        DataFrame du fichier avec une colonne identifiant les
        descriptions ne respectant pas la règle ec4.
    """
    idx = df.loc[(df.loc[:, "FSN_no_sem"].str.contains("fluid sample", regex=False, case=False)) # noqa
                 & (~df.loc[:, "term"].str.contains("échantillon de liquide", regex=False, case=False))].index # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"ec4": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


####################
# Règles Substance #
####################
def _check_su1(df: pd.DataFrame, pt: pd.Series, syn: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle su1-FR.

    args:
        df: DataFrame à valider
        pt: Filtre sur les termes préférés de `df`
        syn: Filtre sur les synonymes acceptables de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les descriptions ne respectant
        pas la règle su1-FR.
    """
    idx = df.loc[pt
                 & (df.loc[:, "FSN_no_sem"].str.contains("(?:antibody|immunoglobulin)", case=False)) # noqa
                 & (~df.loc[:, "FSN_no_sem"].str.contains("immunoglobuline", regex=False, case=False))].index # noqa

    idx = idx.union(df.loc[syn
                           & (df.loc[:, "FSN_no_sem"].str.contains("(?:antibody|immunoglobulin)", case=False)) # noqa
                           & (~df.loc[:, "FSN_no_sem"].str.contains("(?:Ig|anticorps)", case=False))].index) # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"su1": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_su3(df: pd.DataFrame, su: pd.Series, pt: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle su3-FR.

    args:
        df: DataFrame à valider
        su: Filtre sur les Substance de `df`
        pt: Filtre sur les termes préférés de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les descriptions ne respectant
        pas la règle su3-FR.
    """
    idx = df.loc[su & pt
                 & (df.loc[:, "term"].str.contains("(?:méta-|ortho-|para-)", case=False))].index # noqa

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"su3": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df


def _check_su8(df: pd.DataFrame, su: pd.Series, pt: pd.Series) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas la règle su8-FR.

    args:
        df: DataFrame à valider
        su: Filtre sur les Substance de `df`
        pt: Filtre sur les termes préférés de `df`

    returns:
        DataFrame du fichier avec une colonne identifiant les descriptions ne respectant
        pas la règle su8-FR.
    """
    idx = df.loc[su & pt
                 & (df.loc[:, "term"].str.contains("(?:>.*<)", case=False))].index

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={"su8": ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")

    return df

def _check_regle_generique(df: pd.DataFrame, pt: pd.Series, syn: pd.Series, regex_en_fsn: str, regex_fr_term: str, id_regle: str, is_pt: int, is_syn: int) -> pd.DataFrame:
    """Identifie les descriptions ne respectant pas une règle générique sur les articles
    args:        df: DataFrame à valider
        pt: Filtre sur les termes préférés de `df`
        syn: Filtre sur les synonymes acceptables de `df`     
        regex_en_fsn: Expression régulière à appliquer sur la colonne "FSN_no_sem" pour identifier les descriptions ne respectant pas la règle     
        regex_fr_term: Expression régulière à appliquer sur la colonne "term" pour identifier les descriptions respectant la règle     
        id_regle: Identifiant de la règle à ajouter dans le nom de la colonne créée pour identifier les descriptions ne respectant pas la règle     
        is_pt: Indicateur d'application de la règle sur les termes préférés (1 pour appliquer, 0 sinon)     
        is_syn: Indicateur d'application de la règle sur les synonymes acceptables (1 pour appliquer, 0 sinon)  
        
    returns:        DataFrame du fichier avec une colonne identifiant les descriptions ne respectant pas la règle générique.
    """
    idx = pd.Index([])

    if is_pt == 1:
        idx_pt = df.loc[pt
                     & (df.loc[:, "FSN_no_sem"].str.contains(regex_en_fsn, case=False))
                     & (~df.loc[:, "term"].str.contains(regex_fr_term, case=False))].index
        idx = idx.union(idx_pt)
        
    if is_syn == 1:
        idx_syn = df.loc[syn
                        & (df.loc[:, "FSN_no_sem"].str.contains(regex_en_fsn, case=False))
                        & (~df.loc[:, "term"].str.contains(regex_fr_term, case=False))].index
        idx = idx.union(idx_syn)

    idx = idx.union(idx_pt).union(idx_syn)

    if not idx.empty:
        df = pd.merge(df, pd.DataFrame(data={id_regle: ["1"] * len(idx)}, index=idx),
                      how="left", left_index=True, right_index=True, validate="1:1")
    
    return df


def run_editorial_check(
    df: pd.DataFrame,
    rules: pd.DataFrame,
    terminology_anatomica: pd.DataFrame,
    fts: server.Server,
    desc_act_fr: pd.DataFrame 
) -> pd.DataFrame:
    """Lance l'ensemble des contrôles sur le respect des règles éditoriales.

    args:
        df: DataFrame à valider
        rules: DataFrame contenant les règles éditoriales
        fts: Serveur de Terminologies FHIR à utiliser
        desc_act_fr: DataFrame contenant toutes les descriptions actives dans l'edition nationale française

    returns:
        Fichier avec les résultats des contrôles
    """
    print("Vérification des règles éditoriales...", end="\r")
    nb = len(df.columns)

    # Précalcul des lignes PT et SYN
    pt = (df.loc[:, "acceptabilityId"] == "PREFERRED")
    syn = (df.loc[:, "acceptabilityId"] == "ACCEPTABLE")

    # Précalcul des hiérarchies
    # Body structure
    bs = ((df.loc[:, "FSN"].str.endswith(" (body structure)"))
          | (df.loc[:, "FSN"].str.endswith(" (cell)"))
          | (df.loc[:, "FSN"].str.endswith(" (cell structure)"))
          | (df.loc[:, "FSN"].str.endswith(" (morphologic abnormality)")))
    # Body surface region
    bsr = (df.loc[:, "conceptId"].isin(fts.ecl("<< 127947003")))
    # Anatomical structure
    anats = (df.loc[:, "conceptId"].isin(fts.ecl("<< 91723000")))
    # Clinical finding
    co = (df.loc[:, "FSN"].str.endswith(" (finding)"))
    pa = (df.loc[:, "FSN"].str.endswith(" (disorder)"))
    # Pharmaceutical / biological product
    me = (df.loc[:, "conceptId"].isin(fts.ecl("<< 373873005")))
    # Physical object
    sb = (df.loc[:, "conceptId"].isin(fts.ecl("<< 260787004")))
    # Procedure
    pr = ((df.loc[:, "FSN"].str.endswith(" (procedure)"))
          | (df.loc[:, "FSN"].str.endswith(" (regime/therapy)")))
    # Situation with explicit context
    hs = (df.loc[:, "FSN"].str.endswith(" (situation)"))
    # Specimen
    ec = (df.loc[:, "FSN"].str.endswith(" (specimen)"))
    # Substance
    su = (df.loc[:, "FSN"].str.endswith(" (substance)"))

    # Contrôle des espaces inattendus
    df = _check_spaces(df)

    # Contrôle des règles sur l'orthographe de 1990
    df = _check_or4(df)

    # Contrôle des caractères innatendus
    df = _check_chars(df)
    
    # Correction des casses
    # correction = _get_correct_case(df.loc[df.loc[:, "caseSignificanceId"] == "CS"])
    # df.update(correction)
    df = _check_case_significance(df)
    df = _check_spaces(df)
    df = _check_chars(df)

    # Contrôles des règles sur les articles
    df = _check_ar2(df)
    df = _check_ar4_FR(df, bs)
    df = _check_ar6(df, sb)

    # Contrôles des séparateurs et ponctuations
    df = _check_se4(df)

    # Contrôles des règles sur les ligatures
    # df = _check_ll1(df)

    # Contrôle des règles sur l'orthographe de 1990
    df = _check_or4(df)

    # Contrôles des règles de Body Structure
    if not df.loc[bs].empty:
        df = _check_bs2(df, pt)
        df = _check_bs3(df, bs, pt, syn)
        df = _check_bs4(df, anats, terminology_anatomica, pt)
        df = _check_bs5(df, bs, pt, syn)
        df = _check_bs6(df, bs, bsr, pt, syn)
        df = _check_bs7(df, bs, pt, syn)
        df = _check_bs8(df, pt, syn)
        df = _check_bs9(df, pt, syn)
        df = _check_bs10(df, pt, syn)
        df = _check_bs11(df, pt, syn)
        df = _check_bs12(df, pt, syn)
        df = _check_bs13(df)

    # Contrôles des règles de Clinical finding
    if not df.loc[co].empty:
        df = _check_co2(df, co)
        df = _check_co6(df, co)
    if not df.loc[pa].empty:
        df = _check_pa3_1(df)
        df = _check_pa4(df)
        df = _check_pa6(df)
        df = _check_pa7(df)
        df = _check_pa8(df)
        df = _check_pa9(df)

    # Contrôles des règles de Pharmaceutical / biological product
    if not df.loc[me].empty:
        df = _check_me1(df, me)
        df = _check_me2(df, me)
        df = _check_me3(df, me)
        df = _check_me4(df, me)

    # Contrôles des règles de Physical object
    if not df.loc[sb].empty:
        df = _check_sb1(df)
        df = _check_sb2(df)
        df = _check_sb3(df, pt, syn)

    # Contrôles des règles de Procedure
    if not df.loc[pr].empty:
        df = _check_pr2(df, pt, syn)
        df = _check_pr3(df)
        df = _check_pr4(df, pt, syn)
        df = _check_pr9(df, pt, syn)
        df = _check_pr10(df)
        df = _check_pr12(df, pt, syn)
        df = _check_pr13(df, pt, syn)
        df = _check_pr14(df, pt, syn)
        df = _check_pr15(df, pr)

    # Contrôles des règles de Situation with explicit context
    if not df.loc[hs].empty:
        df = _check_hs1(df, hs)

    # Contrôles des règles de Specimen
    if not df.loc[ec].empty:
        df = _check_ec2(df)
        df = _check_ec4(df)

    # Contrôles des règles de Substance
    if not df.loc[su].empty:
        df = _check_su1(df, pt, syn)
        df = _check_su3(df, su, pt)
        df = _check_su8(df, su, pt)

    # Règles génériques issues du fichier rules.csv
    for _, rule in rules.iterrows():
        df = _check_regle_generique(df, pt, syn, rule["en"], rule["fr"], rule["id"], rule["pt"], rule["syn"])

    df = _check_unicity(df, desc_act_fr)

    nb = len(df.columns) - nb
    status = "OK" if nb == 0 else "KO"
    print(f"{nb} règle(s) éditoriales non respectées - {status}")

    return df
