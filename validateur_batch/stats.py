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
    for section in scope.sections:
        print(f"Nombre de concepts commandés dans la section '{section}' : {len(scope.get_section_df(section))}")

    print(f"Nombre de concepts dans les fichiers livrés : {preview.loc[preview['source'] == 'delivery', 'conceptId'].nunique()}")

    df_nb_existing_descs = preview[["conceptId", "id"]].groupby("conceptId").agg("count").reset_index()
    concepts_with_existing_descs = df_nb_existing_descs.loc[df_nb_existing_descs["id"] > 0, "conceptId"]
    print(f"Nombre de concepts avec au moins une description dans la version précédente : {len(concepts_with_existing_descs)}")

    nb_val_concepts = preview.loc[preview["_type_"] == "VAL", "conceptId"].unique()
    print("Nombre de concepts déjà traduits dans une version précédente, "
          + f"revus et ne nécessitant pas de modification : {len(nb_val_concepts)}")

    preview_existing_descs = preview.loc[preview["conceptId"].isin(concepts_with_existing_descs)]
    df_modified_descs = preview_existing_descs.loc[(~preview_existing_descs["_type_"].isin(["", "VAL"]))]
    modified_concepts  = df_modified_descs["conceptId"].unique()
    nb_concepts_modified = len(modified_concepts)
    print(f"Nombre de concepts déjà traduits dans la version précédente et désormais modifiés : {nb_concepts_modified}")


    nb_concepts_new = len(df_nb_existing_descs.loc[df_nb_existing_descs["id"] == 0])
    print(f"Nombre de concepts sans traduction dans la version précédente et désormais traduits : {nb_concepts_new}")









