import pandas as pd

from typing import Literal, TYPE_CHECKING
from validateur_batch.control import format_check

if TYPE_CHECKING:
    from validateur_batch.object import server

BATCH_TYPE = Literal["VAL", "ADD", "CHG", "REP", "INA"]
COL = {
    "VAL": ["Concept ID", "FSN"],
    "ADD": ["Concept ID", "GB/US FSN Term (For reference only)",
            "Preferred Term (For reference only)", "Translated Term", "Language Code",
            "Case significance", "Type", "Language reference set", "Acceptability"],
    "CHG": ["Description ID", "Preferred Term (For reference only)",
            "Term (For reference only)", "Case significance", "Type",
            "Language reference set", "Acceptability"],
    "REP": ["Concept ID", "Description ID", "Preferred Term (For reference only)",
            "Term (For reference only)", "Inactivation Reason",
            "Association Target ID1", "Association Target ID2",
            "Association Target ID3", "Association Target ID4",
            "New Replacement Description ID", "Replacement term (For reference only)",
            "New Translated Term", "Language Code", "Case significance", "Type",
            "Language reference set", "Acceptability"],
    "INA": ["Description ID Or Term",
            "Language Code (require if the term is specified)", "Concept ID (Optional)",
            "Preferred Term (For reference only)", "Term (For reference only)",
            "Inactivation Reason", "Association Target ID1", "Association Target ID2",
            "Association Target ID3", "Association Target ID4"]
}


class Batch:
    """Représente un batch de descriptions à ajouter, modifier, inactiver ou remplacer
    dans l'Authoring Platform ainsi que les résultats des contrôles associés"""
    def __init__(self, file: str, type: BATCH_TYPE):
        # Métadonnées du batch
        self.file = file
        self.type = type
        # Données du batch
        self.df = pd.read_csv(file, sep=";", quoting=3, na_filter=False, dtype=str)

        if not all(i == j for i, j in zip(self.df.columns, COL[type])):
            diff = [i for i, j in zip(self.df.columns, COL[type]) if i != j]
            raise ValueError(f"Colonne(s) du fichier incorrecte(s) : {file} {diff}")

    def _apply_add(self, preview: pd.DataFrame) -> pd.DataFrame:
        """Applique les modifications d'un batch d'addition à `preview`

        args:
            preview: DataFrame contenant les descriptions d'intérêt de la snapshot dans
                le périmètre des travaux

        returns:
            DataFrame avec les nouvelles descriptions ajoutées par le batch
        """
        # Identifier l'addition de PT pour des concepts en ayant déjà
        pt = preview.loc[preview.loc[:, "conceptId"].isin(
            self.df.loc[self.df.loc[:, "Acceptability"] == "PREFERRED", "Concept ID"])]
        # Modifier l'acceptabilité des PT existants
        pt.loc[:, "acceptabilityId"] = ["ACCEPTABLE"] * len(pt)
        preview.update(pt)

        # Formatage du batch à ajouter
        add = self.df.loc[:, ["Concept ID", "Translated Term", "Case significance",
                              "Acceptability"]]
        add.columns = ["conceptId", "term", "caseSignificanceId",
                       "acceptabilityId"]
        add.loc[:, "_type_"] = ["ADD"] * len(add)
        add.loc[:, "active"] = ["1"] * len(add)

        # Ajout des descriptions du batch
        preview.reset_index(inplace=True)
        preview = pd.concat([preview, add], ignore_index=True)
        preview.set_index("id", inplace=True)

        return preview

    def _apply_chg(self, preview: pd.DataFrame) -> pd.DataFrame:
        """Applique les modifications d'un batch de changement à `preview`

        args:
            preview: DataFrame contenant les descriptions d'intérêt de la snapshot dans
                le périmètre des travaux

        returns:
            DataFrame avec la mise à jour des métadonnées du batch
        """
        # Formatage des changements de métadonnées
        chg = self.df.loc[:, ["Description ID", "Case significance", "Acceptability"]]
        chg.set_index("Description ID", inplace=True)
        chg.columns = ["caseSignificanceId", "acceptabilityId"]
        chg.loc[:, "_type_"] = ["CHG"] * len(chg)

        # Changement des descriptions du batch
        preview.update(chg)

        return preview

    def _apply_rep(self, preview: pd.DataFrame) -> pd.DataFrame:
        """Applique les modifications d'un batch de remplacement à `preview`

        args:
            preview: DataFrame contenant les descriptions d'intérêt de la snapshot dans
                le périmètre des travaux

        returns:
            DataFrame avec le remplacement des descriptions du batch
        """
        rep = self.df.loc[
            :,
            [
                "Concept ID",
                "Description ID",
                "New Translated Term",
                "Case significance",
                "Acceptability",
                "New Replacement Description ID",
            ],
        ]

        # Inactivation des descriptions à remplacer
        ina = rep[["Description ID"]].rename(columns={"Description ID": "id"})
        ina["active"] = "0"
        ina["_type_"] = "INA"
        ina.set_index("id", inplace=True)
        preview.update(ina)

        # Ajout des descriptions de remplacement
        add = (
            rep.loc[rep["New Replacement Description ID"].str.len() == 0]
            .rename(
                columns={
                    "Description ID": "id",
                    "New Translated Term": "term",
                    "Concept ID": "conceptId",
                    "Case significance": "caseSignificanceId",
                    "Acceptability": "acceptabilityId",
                }
            )
            .set_index("id")
        )
        add["active"] = "1"
        add["_type_"] = "REP"
        preview.update(add)

        # Promotion des descriptions de remplacement existantes
        promote = (
            rep.loc[rep["New Replacement Description ID"].str.len() > 0]
            .rename(columns={"New Replacement Description ID": "id"})
            .set_index("id")
        )
        promote["_type_"] = "REP"
        promote["acceptabilityId"] = "PREFERRED"
        preview.update(promote)

        return preview

    def _apply_ina(self, preview: pd.DataFrame) -> pd.DataFrame:
        """Applique les modifications d'un batch d'inactivation à `preview`

        args:
            preview: DataFrame contenant les descriptions d'intérêt de la snapshot dans
                le périmètre des travaux

        returns:
            DataFrame avec l'inactivation des descriptions du batch
        """
        # Formatage des inactivations du batch
        ina = self.df.loc[:, ["Description ID Or Term"]]
        ina.loc[:, "active"] = ["0"] * len(ina)
        ina.loc[:, "_type_"] = ["INA"] * len(ina)
        ina.set_index("Description ID Or Term", inplace=True)

        # Inactivation des descriptions du batch
        preview.update(ina)

        return preview

    def apply_modif(self, preview: pd.DataFrame) -> None:
        """
        Applique les modifications du batch à `preview`

        args:
            preview: DataFrame contenant les descriptions d'intérêt de la snapshot
                FR dans le périmètre des travaux

        returns:
            DataFrame `preview` mis à jour avec les modifications des batchs
        """
        self.df.reset_index(inplace=True)
        self.df.loc[:, "_type_"] = [""] * len(self.df)
        print(f"{self.type} - Application des modifications à la Snapshot...",
              end="\r")
        match self.type:
            case "ADD":
                preview = self._apply_add(preview)
            case "CHG":
                preview = self._apply_chg(preview)
            case "REP":
                preview = self._apply_rep(preview)
            case "INA":
                preview = self._apply_ina(preview)
        print(f"{self.type} - Application des modifications à la Snapshot - OK")

        return preview

    def check_format(self, fts: "server.Server") -> pd.DataFrame:
        """Lance les contrôles de format du fichier batch.

        args:
            fts: Serveur de Terminologies FHIR à utiliser
        """
        print(f"{self.type} - Vérification du format...", end="\r")
        nb = len(self.df.columns)
        self.df = format_check.run_format_check(self.df, self.type, fts)
        nb = len(self.df.columns) - nb
        status = "OK" if nb == 0 else "KO"
        print(f"{self.type} - {nb} règle(s) de format non respectées - {status}")
        return self.df
