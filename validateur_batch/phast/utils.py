import os.path as op
import pandas as pd

SHORT_ACCEPTABILITY = {
    "PREFERRED": "PT",
    "ACCEPTABLE": "SA"
}

def generate_excel_from_report(csv_path: str, excel_path: str) -> None:
    """Génération d'un fichier excel, condensé du résultat, pour intégration dans le fichier de travail

    args:
        csv_path: Chemin vers check_results.csv.
        excel_path: Chemin vers le fichier Excel de destination.
    """
    df_chk_results = pd.read_csv(csv_path, sep=";", dtype={"conceptId": "string"} )
    df_chk_results = df_chk_results[df_chk_results["active"]=="1"]  # on ne garde que les concepts actifs
    
    rules_columns = [col for col in list(df_chk_results.columns) if col not in ["id", "active", "_type_", "conceptId", "FSN", "FSN_no_sem", "term", "caseSignificanceId", "acceptabilityId"]]
    all_conceptIds = df_chk_results["conceptId"].unique()
    
    df_condense = pd.DataFrame({
        "conceptId": pd.Series(dtype="string"),
        "FSN": pd.Series(dtype="string"),
        "preferred term fr": pd.Series(dtype="string"),
        "SA1 fr": pd.Series(dtype="string"),
        "SA2 fr": pd.Series(dtype="string"),
        "SA3 fr": pd.Series(dtype="string"),
        "SA4 fr": pd.Series(dtype="string"),
        "SA5 fr": pd.Series(dtype="string"),
        "SA6 fr": pd.Series(dtype="string"),
        "SA7 fr": pd.Series(dtype="string"),
        "SA8 fr": pd.Series(dtype="string"),
        "SA9 fr": pd.Series(dtype="string"),
        "SA10 fr": pd.Series(dtype="string"),
        "errors": pd.Series(dtype="string"),
        "errors_PT": pd.Series(dtype="string"),
        "errors_AS1": pd.Series(dtype="string"),
        "errors_AS2": pd.Series(dtype="string"),
        "errors_AS3": pd.Series(dtype="string"),
        "errors_AS4": pd.Series(dtype="string"),
        "errors_AS5": pd.Series(dtype="string"),
        "errors_AS6": pd.Series(dtype="string"),
        "errors_AS7": pd.Series(dtype="string"),
        "errors_AS8": pd.Series(dtype="string"),
        "errors_AS9": pd.Series(dtype="string")
    })

    for conceptId in all_conceptIds:
        df_concept = df_chk_results[df_chk_results["conceptId"] == conceptId]
        termes_en_erreur  = ""
        regles_en_erreur = list()
        preferred_term_fr = df_concept[df_concept["acceptabilityId"]=="PREFERRED"]["term"].iloc[0] if len(df_concept[df_concept["acceptabilityId"]=="PREFERRED"]) > 0 else pd.NA
        sa1_fr = df_concept[df_concept["acceptabilityId"]=="ACCEPTABLE"]["term"].iloc[0] if len(df_concept[df_concept["acceptabilityId"]=="ACCEPTABLE"]) > 0 else pd.NA
        sa2_fr = df_concept[df_concept["acceptabilityId"]=="ACCEPTABLE"]["term"].iloc[1] if len(df_concept[df_concept["acceptabilityId"]=="ACCEPTABLE"]) > 1 else pd.NA
        sa3_fr = df_concept[df_concept["acceptabilityId"]=="ACCEPTABLE"]["term"].iloc[2] if len(df_concept[df_concept["acceptabilityId"]=="ACCEPTABLE"]) > 2 else pd.NA
        sa4_fr = df_concept[df_concept["acceptabilityId"]=="ACCEPTABLE"]["term"].iloc[3] if len(df_concept[df_concept["acceptabilityId"]=="ACCEPTABLE"]) > 3 else pd.NA
        sa5_fr = df_concept[df_concept["acceptabilityId"]=="ACCEPTABLE"]["term"].iloc[4] if len(df_concept[df_concept["acceptabilityId"]=="ACCEPTABLE"]) > 4 else pd.NA
        sa6_fr = df_concept[df_concept["acceptabilityId"]=="ACCEPTABLE"]["term"].iloc[5] if len(df_concept[df_concept["acceptabilityId"]=="ACCEPTABLE"]) > 5 else pd.NA
        sa7_fr = df_concept[df_concept["acceptabilityId"]=="ACCEPTABLE"]["term"].iloc[6] if len(df_concept[df_concept["acceptabilityId"]=="ACCEPTABLE"]) > 6 else pd.NA
        sa8_fr = df_concept[df_concept["acceptabilityId"]=="ACCEPTABLE"]["term"].iloc[7] if len(df_concept[df_concept["acceptabilityId"]=="ACCEPTABLE"]) > 7 else pd.NA
        sa9_fr = df_concept[df_concept["acceptabilityId"]=="ACCEPTABLE"]["term"].iloc[8] if len(df_concept[df_concept["acceptabilityId"]=="ACCEPTABLE"]) > 8 else pd.NA
        sa10_fr = df_concept[df_concept["acceptabilityId"]=="ACCEPTABLE"]["term"].iloc[9] if len(df_concept[df_concept["acceptabilityId"]=="ACCEPTABLE"]) > 9 else pd.NA

        for _, row in df_concept.iterrows():
            mask = row[rules_columns] == 1
            if mask.any():
                colonnes_en_erreur = mask[mask].index.tolist()   # seules les colonnes à True
                term_erreurs = f"{row['term']} ({SHORT_ACCEPTABILITY[row['acceptabilityId']]}) : {', '.join(colonnes_en_erreur)}"
                regles_en_erreur.append(term_erreurs)
            else:
                continue    

        termes_en_erreur += " | ".join(regles_en_erreur)    
        
        df_condense.loc[len(df_condense)] = [
                    conceptId,
                    df_concept["FSN"].iloc[0],
                    preferred_term_fr,
                    sa1_fr,
                    sa2_fr,
                    sa3_fr,
                    sa4_fr,
                    sa5_fr,
                    sa6_fr,
                    sa7_fr,
                    sa8_fr,
                    sa9_fr,
                    sa10_fr,
                    termes_en_erreur, 
                    pd.NA,
                    pd.NA,
                    pd.NA,
                    pd.NA,
                    pd.NA,
                    pd.NA,
                    pd.NA,
                    pd.NA,
                    pd.NA,
                    pd.NA
                    ]
       
    df_condense.to_excel(excel_path, index=False)
    print(f"Fichier Excel généré : {excel_path}")
