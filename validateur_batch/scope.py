import json
import pandas as pd
from validateur_batch.object import server

class Scope:
    """
    Classe représentant le périmètre d'analyse, c'est-à-dire l'ensemble des concepts SNOMED CT
    sur lesquels les vérifications seront effectuées.

    Attributes:
        df (pd.DataFrame): DataFrame contenant les concepts du périmètre d'analyse
          avec les colonnes "section", "conceptId" et "fsn".

    """
    def __init__(self, scope_file: str, fts: server.Server):
        with open(scope_file, "r") as f:
            self.definitions = json.load(f)
        self.fts = fts
        self._sections={}
        self._full_scope_df = None

    def get_section_df(self, section_name: str) -> pd.DataFrame:
        """
        Construit un DataFrame contenant les concepts d'une section spécifique du périmètre d'analyse.

        Args:
            section_name (str): Nom de la section à extraire.

        Returns:
            pd.DataFrame: DataFrame contenant les concepts de la section spécifiée
            avec les colonnes "section", "conceptId" et "fsn".

        Raises:
            ValueError: Si la section spécifiée n'est pas trouvée dans le périmètre d'analyse.
        """
        # check if cache exists
        if section_name in self._sections:
            return self._sections[section_name]
        
        # compute section df
        section = next((s for s in self.definitions if s["name"] == section_name), None)
        if section is None:
            raise ValueError(f"Section '{section_name}' non trouvée dans le périmètre d'analyse.")
        section_df = pd.DataFrame(columns=["section", "conceptId", "fsn"])
        concepts = self.fts.ecl(section["ecl"])
        section_df["conceptId"] = concepts
        section_df["fsn"] = section_df["conceptId"].apply(
            lambda x: self.fts.get_fsn(x)
        )
        section_df["section"] = [section_name]* len(section_df)

        # cache the result
        self._sections[section_name] = section_df

        return section_df

    @property
    def sections(self) -> list:
        """ Retourne la liste des sections définies dans le périmètre d'analyse. Returns: list: Liste des noms de sections définies dans le périmètre d'analyse. """
        return [section["name"] for section in self.definitions["sections"]]

    @property
    def full_scope_df(self) -> pd.DataFrame:
        """
        Construit un DataFrame contenant les concepts constituant le périmètre d'analyse 
        à partir de la définition du périmètre et du FTS.

        Returns:
            pd.DataFrame: DataFrame contenant les concepts du périmètre d'analyse
            avec les colonnes "section", "conceptId" et "fsn".

        """
        if self._full_scope_df is not None: 
            return self._full_scope_df
        section_dfs = []
        for section in self.definitions:
            section_df = self.get_section_df(section["name"])
            section_dfs.append(section_df)
        self._full_scope_df = pd.concat(section_dfs, ignore_index=True)
        return self._full_scope_df
