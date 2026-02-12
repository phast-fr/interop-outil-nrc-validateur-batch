import pandas as pd
from validateur_batch.scope import Scope

def print_stats(scope: Scope, preview: pd.DataFrame, batches: list):
    """
    Affiche les statistiques de vérifications de manière lisible.

    Args:
        stats (pd.DataFrame): DataFrame contenant les statistiques calculées, avec une ligne par vérification
          et les colonnes "check", "total", "passed", "failed" et "pass_rate".

    """
    if scope is None:
        print("Périmètre d'analyse non défini. Impossible d'afficher les statistiques de vérifications.") 
        return
    
    print(f"Nombre de concepts dans le périmètre commandé : {len(scope.full_scope_df)}")
    print(f"Nombre de concepts dans les fichiers livrés : {preview['conceptId'].nunique()}")

    b_val = next((b for b in batches if b.type == "VAL"), None)
    if b_val is not None:
        df_val = b_val.df
        print("Nombre de concepts déjà traduits dans une version précédente, "
              + f"revus et ne nécessitant pas de modification : {len(df_val)}")

    df_nb_existing_descs = preview[["conceptId", "id"]].groupby("conceptId").agg("count").reset_index()
    nb_concepts_new = len(df_nb_existing_descs.loc[df_nb_existing_descs["id"] == 0])
    print(f"Nombre de concepts nouvellement traduits : {nb_concepts_new}")






