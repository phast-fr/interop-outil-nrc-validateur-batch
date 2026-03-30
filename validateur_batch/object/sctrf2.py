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

class SctEd :
    """
    Classe de lecture des RF2 d'une édition SNOMED CT internationale
    """

    def __init__(self, path: str, cache: str):
        self.root = Path(path)
        if not self.root.exists():
            raise ValueError()
        self._read_version()
        if not self._load_from_cache(cache):
            self._load_from_rf2()
            self._save_to_cache(cache)

    def _read_version(self):
        logger.debug(f"lecture de la version depuis {self.root}")
        # lecture de la version
        pi_path = self.root / PACKAGE_INFO_REL_PATH
        with open(pi_path) as f:
            pi = json.load(f)
        self.version = pi["effectiveTime"]
        logger.debug(f"version : {self.version}")

    def _load_from_cache(self, cache_root):
        cache = Path(cache_root) / self.version
        if (cache).exists():
            self.df_concept = pd.read_parquet(cache / "concept.parquet")
            self.df_description = pd.read_parquet(cache / "description.parquet")
            self.df_refset = pd.read_parquet(cache / "refset.parquet")
            self.df_fsn = pd.read_parquet(cache / "fsn.parquet")
            self.df_pten = pd.read_parquet(cache / "pten.parquet")

            return True
        else:
            return False
        
    def _save_to_cache(self, cache_root):
        cache = Path(cache_root) / self.version
        cache.mkdir(parents=True, exist_ok=True)
        self.df_concept.to_parquet(cache / "concept.parquet")
        self.df_description.to_parquet(cache / "description.parquet")
        self.df_refset.to_parquet(cache / "refset.parquet")
        self.df_fsn.to_parquet(cache / "fsn.parquet")
        self.df_pten.to_parquet(cache / "pten.parquet")

    def _load_from_rf2(self):
        logger.debug("chargement des concepts")
        concept_path = self.root / CONCEPT_REL_PATH.format(version=self.version)
        self.df_concept = (
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
        self.df_description = pd.read_csv(
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
        self.df_refset = pd.read_csv(
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
            self.df_refset
            .loc[
                (self.df_refset["refsetId"]=="US") &
                (self.df_refset["active"]=="1")
            ]
            .drop(columns=["active"])
        )
        self.df_desc_us = (
            self.df_description
            .loc[self.df_description["active"]=="1"]
            .merge(
                df_us,
                how="left",
                left_on="id",
                right_on="referencedComponentId"
            )
            .drop(columns=["referencedComponentId"])
        )

        self.df_fsn = (
            self.df_desc_us.loc[
                (self.df_desc_us["active"]=="1") &
                (self.df_desc_us["typeId"]=="FSN")
                ,
                ["conceptId", "term"]
            ]
            .set_index("conceptId", verify_integrity=True)
            .sort_index()
            .rename(columns={"term": "fsn"})
        )

        self.df_pten = (
            self.df_desc_us.loc[
                (self.df_desc_us["active"]=="1") &
                (self.df_desc_us["typeId"]=="SYN") &
                (self.df_desc_us["acceptabilityId"]=="PREFERRED")
                ,
                ["conceptId", "term"]
            ]
            .set_index("conceptId", verify_integrity=True)
            .sort_index()
            .rename(columns={"term": "pten"})
        )

        logger.debug("fin du chargement")

    def get_fsn(self, conceptId: str) -> str:
        fsn = self.df_fsn.loc[conceptId, "fsn"]
        return fsn
        
    def get_pten(self, conceptId: str) -> str:
        pten = self.df_pten.loc[conceptId, "pten"]
        return pten
    
    def is_active(self, conceptId: str) -> bool:
        active = self.df_concept.loc[conceptId, "active"]
        return (active == "1")