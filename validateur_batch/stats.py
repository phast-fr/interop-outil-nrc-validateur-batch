import pandas as pd
from validateur_batch.scope import Scope

def print_stats(scope: Scope, preview: pd.DataFrame):
    """
    Affiche les statistiques de vérifications de manière lisible.

    Args:
        stats (pd.DataFrame): DataFrame contenant les statistiques calculées, avec une ligne par vérification
          et les colonnes "check", "total", "passed", "failed" et "pass_rate".

    """
    pass
