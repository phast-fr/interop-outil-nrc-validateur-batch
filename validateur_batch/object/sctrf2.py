import logging
from pathlib import Path
import json
import csv
import pandas as pd
logger = logging.getLogger(__name__)

CASE = {
    "900000000000448009": "ci",
    "900000000000017005": "CS",
    "900000000000020002": "cI"
}

ACCEPT = {
    "900000000000548007": "PREFERRED",
    "900000000000549004": "ACCEPTABLE"
}

TYPE = {
    "900000000000013009": "SYN",
    "900000000000003001": "FSN"
}

REFSET = {
    "900000000000509007": "US",
    "900000000000508004": "GB"
}

# Fichiers utilisés dans la distribution SNOMED CT
PACKAGE_INFO_REL_PATH="release_package_information.json"
CONCEPT_REL_PATH="Snapshot/Terminology/sct2_Concept_Snapshot_INT_{version}.txt"
DESCRIPTION_REL_PATH="Snapshot/Terminology/sct2_Description_Snapshot-en_INT_{version}.txt"
REFSET_REL_PATH="Snapshot/Refset/Language/der2_cRefset_LanguageSnapshot-en_INT_{version}.txt"

class SctEd:
    """
    Lecture des fichiers RF2 d'une édition SNOMED CT internationale.

    Au premier chargement, lit les fichiers RF2 depuis le répertoire de distribution
    et sérialise les données utiles en parquet dans le répertoire de cache. Aux
    exécutions suivantes, charge directement depuis le cache pour éviter de relire
    les fichiers RF2 volumineux.

    Attributes:
        root (Path): Chemin racine de la distribution RF2 internationale.
        version (str): Version de l'édition (effectiveTime lu dans release_package_information.json).
        df (pd.DataFrame): DataFrame indexé par conceptId avec les colonnes :
            - ``active`` : statut d'activité du concept (« 1 » ou « 0 »),
            - ``fsn`` : FSN anglais actif du concept,
            - ``pten`` : preferred term anglais (US) actif du concept.
    """

    def __init__(self, path: str, cache: str):
        """
        Initialise l'édition SNOMED CT internationale.

        Args:
            path: Chemin vers le répertoire racine de la distribution RF2 (contient
                  release_package_information.json).
            cache: Chemin vers le répertoire de cache parquet. Un sous-répertoire
                   nommé d'après la version est créé automatiquement.

        Raises:
            ValueError: Si le répertoire ``path`` n'existe pas.
        """
        self.root = Path(path)
        if not self.root.exists():
            raise ValueError()
        self._read_version()
        if not self._load_from_cache(cache):
            self._load_from_rf2()
            self._save_to_cache(cache)

    def _read_version(self):
        """Lit la version de l'édition depuis release_package_information.json."""
        logger.debug(f"lecture de la version depuis {self.root}")
        # lecture de la version
        pi_path = self.root / PACKAGE_INFO_REL_PATH
        with open(pi_path) as f:
            pi = json.load(f)
        self.version = pi["effectiveTime"]
        logger.debug(f"version : {self.version}")

    def _load_from_cache(self, cache_root) -> bool:
        """
        Tente de charger le DataFrame depuis le cache parquet.

        Args:
            cache_root: Répertoire racine du cache. Le sous-répertoire correspondant
                        à la version courante doit exister pour que le chargement réussisse.

        Returns:
            True si le cache existait et a été chargé, False sinon.
        """
        cache = Path(cache_root) / self.version
        if (cache).exists():
            self.df = pd.read_parquet(cache / "concepts.parquet")
            return True
        else:
            return False

    def _save_to_cache(self, cache_root):
        """
        Sérialise le DataFrame en parquet dans le répertoire de cache.

        Le sous-répertoire ``<cache_root>/<version>`` est créé si nécessaire.

        Args:
            cache_root: Répertoire racine du cache.
        """
        cache = Path(cache_root) / self.version
        cache.mkdir(parents=True, exist_ok=True)
        self.df.to_parquet(cache / "concepts.parquet")

    def _load_from_rf2(self):
        """
        Charge les données depuis les fichiers RF2 de la distribution SNOMED CT.

        Lit les fichiers de concepts, descriptions et language refsets, puis construit
        le DataFrame ``self.df`` (indexé par conceptId) avec les colonnes ``active``,
        ``fsn`` et ``pten``.
        """
        logger.debug("chargement des concepts")
        concept_path = self.root / CONCEPT_REL_PATH.format(version=self.version)
        df_concept = (
            pd.read_csv(
            concept_path
            , sep="\t"
            , encoding='utf-8'
            , quoting=csv.QUOTE_NONE
            , keep_default_na=False
            , usecols=["id", "active"]
            , dtype={"id": str, "active": pd.CategoricalDtype(["1", "0"])}
            )
            .set_index("id", verify_integrity=True)
            .sort_index()
        )

        logger.debug("chargement des descriptions")
        description_path = self.root / DESCRIPTION_REL_PATH.format(version=self.version)
        df_description = pd.read_csv(
            description_path,
            sep="\t",
            quoting=csv.QUOTE_NONE,
            na_filter=False,
            usecols=[
                "id",
                "active",
                "conceptId",
                "typeId",
                "term",
                "caseSignificanceId",
            ],
            dtype={
                "id": str,
                "active": pd.CategoricalDtype(["1", "0"]),
                "conceptId": str,
                "term": str,
            },
            converters={
                "caseSignificanceId": CASE.get,
                "typeId": TYPE.get
            },
        )

        logger.debug("chargement des refsets")
        refset_path = self.root / REFSET_REL_PATH.format(version=self.version)
        df_refset = pd.read_csv(
            refset_path,
            sep="\t",
            na_filter=False,
            usecols=["refsetId", "referencedComponentId", "acceptabilityId", "active"],
            dtype={
                "referencedComponentId": str,
                "active": pd.CategoricalDtype(["1", "0"]),
            },
            converters={
                "acceptabilityId": ACCEPT.get,
                "refsetId": REFSET.get
            },
        )

        logger.debug("préparation des versions condensées")
        df_us = (
            df_refset
            .loc[
                (df_refset["refsetId"]=="US") &
                (df_refset["active"]=="1")
            ]
            .drop(columns=["active"])
        )
        df_desc_us = (
            df_description
            .loc[df_description["active"]=="1"]
            .merge(
                df_us,
                how="left",
                left_on="id",
                right_on="referencedComponentId"
            )
            .drop(columns=["referencedComponentId"])
        )

        df_fsn = (
            df_desc_us.loc[
                (df_desc_us["active"]=="1") &
                (df_desc_us["typeId"]=="FSN")
                ,
                ["conceptId", "term"]
            ]
            .set_index("conceptId", verify_integrity=True)
            .sort_index()
            .rename(columns={"term": "fsn"})
        )

        df_pten = (
            df_desc_us.loc[
                (df_desc_us["active"]=="1") &
                (df_desc_us["typeId"]=="SYN") &
                (df_desc_us["acceptabilityId"]=="PREFERRED")
                ,
                ["conceptId", "term"]
            ]
            .set_index("conceptId", verify_integrity=True)
            .sort_index()
            .rename(columns={"term": "pten"})
        )

        self.df = df_concept.join(df_fsn).join(df_pten)

        logger.debug("fin du chargement")

    def get_fsn(self, conceptId: str) -> str:
        """
        Retourne le FSN anglais actif d'un concept.

        Args:
            conceptId: Identifiant SNOMED CT du concept.

        Returns:
            Le FSN du concept.
        """
        return self.df.loc[conceptId, "fsn"]

    def get_pten(self, conceptId: str) -> str:
        """
        Retourne le preferred term anglais (US) actif d'un concept.

        Args:
            conceptId: Identifiant SNOMED CT du concept.

        Returns:
            Le preferred term anglais du concept.
        """
        return self.df.loc[conceptId, "pten"]

    def is_active(self, conceptId: str) -> bool:
        """
        Indique si un concept est actif.

        Args:
            conceptId: Identifiant SNOMED CT du concept.

        Returns:
            True si le concept est actif, False sinon.
        """
        return (self.df.loc[conceptId, "active"] == "1")
