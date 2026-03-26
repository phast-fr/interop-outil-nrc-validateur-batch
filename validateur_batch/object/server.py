import jsonpath
import requests
from typing import Dict, List
import pandas as pd

INACTIVE_STATUS = 0
ACTIVE_STATUS = 1
NOT_FOUND_STATUS = None

from typing import Dict, List
import pandas as pd

INACTIVE_STATUS = 0
ACTIVE_STATUS = 1
NOT_FOUND_STATUS = None

class Server:
    """
    Classe regroupant les interactions avec le serveur de Terminologies FHIR de votre
    choix
    """

    def __init__(
        self,
        endpoint: str,
        login: str = None,
        password: str = None,
        versioning: bool = True,
        cache_file: str = None,
    ):
        """
        Args:
            endpoint: Endpoint de votre serveur de Terminologies FHIR
            cache_file: Fichier de cache pour les données récupérées du FTS (si vide, le FTS est utilisé pour chaque requête)
        """
        self.endpoint = endpoint
        self.login = login
        self.password = password

        self.session = requests.Session()

        if cache_file is not None:
            self.cache = pd.read_csv(cache_file, dtype=str)
        else:
            self.cache = None

        if versioning:
            self.ecl_base_url = f"{endpoint}/ValueSet/$expand?url=http://snomed.info/sct/900000000000207008?fhir_vs=ecl/"  # noqa
            self.lookup_base_url = f"{endpoint}/CodeSystem/$lookup?system=http://snomed.info/sct&version=http://snomed.info/sct/900000000000207008"  # noqa
        else:
            self.ecl_base_url = f"{endpoint}/ValueSet/$expand?url=http://snomed.info/sct?fhir_vs=ecl/"  # noqa
            self.lookup_base_url = (
                f"{endpoint}/CodeSystem/$lookup?system=http://snomed.info/sct"  # noqa
            )

    def ecl(self, ecl: str) -> List[str]:
        """Envoie une requête ECL au FTS

        Args:
            ecl: Requête ECL

        Returns:
            Liste des SCTID correspondant à la requête ECL
        """
        url = f"{self.endpoint}/ValueSet/$expand"
        params = {
            "offset": 0,
            "url": f"http://snomed.info/sct/900000000000207008?fhir_vs=ecl/{ecl}",  # noqa
        }
        codes = []
        while True:
            response = self.session.request(
                "GET",
                url,
                params=params,
                auth=(self.login, self.password)
                if self.login and self.password
                else None,
            )
            response.raise_for_status()
            with open(f"output/reponse_ecl_{params["offset"]}.json", "w") as file:
                file.write(response.text)
            total = jsonpath.match(
                "$.expansion.total",
                response.text,
            ).obj
            page_codes = jsonpath.findall(
                "$.expansion.contains[*].code",
                response.text,
            )
            codes.extend(page_codes)
            if len(codes) < total:
                params["offset"] = len(codes)
            else:
                break

        return codes


    def _sctid_is_inactive(self, json: Dict) -> bool:
        """Vérifie si le concept est inactif

        args:
            json: Résultat de l'opération lookup

        returns:
            True si le concept est inactif, False sinon
        """
        p = list(
            jsonpath.query(
                "$.parameter[?@name == 'property'].part[?@valueCode == 'inactive']",
                json,
            ).pointers()  # noqa
        )[0]

        is_inactive = next(
            filter(lambda x: x["name"] == "value", p.resolve_parent(json)[0])
        )["valueBoolean"]

        return is_inactive

    def lookup(self, sctid: str) -> str:
        """Renvoie les informations d'un concept SNOMED CT

        Args:
            sctid: SCTID du concept

        Returns:
            Informations du concept `sctid`
        """
        url = f"{self.lookup_base_url}&code={sctid}"

        response = self.session.request(
            "GET",
            url,
            auth=(self.login, self.password)
            if self.login and self.password
            else None,
        )
        response.raise_for_status()

        return response.json()

    def get_status(self, sctid: str) -> int | None:
        """Donne le statut du concept `sctid`

        args:
            sctid: SCTID du concept

        returns:
            Statut du concept `sctid` :
                - 1 : actif
                - 0 : inactif
                - None : concept non trouvé
        """
        if self.cache is not None:
            if sctid in self.cache["conceptId"].values:
                return ACTIVE_STATUS

        json = self.lookup(sctid)
        if self._sctid_is_inactive(json):
            return INACTIVE_STATUS
        else:
            return ACTIVE_STATUS

    def get_fsn(self, sctid: str) -> str:
        """Donne le FSN du concept `sctid`

        args:
            sctid: SCTID du concept

        returns:
            FSN du concept
        """
        if self.cache is not None:
            fsn = self.cache.loc[self.cache["conceptId"] == sctid, "fsn/term"]
            if not fsn.empty:
                return fsn.iloc[0]

        json = self.lookup(sctid)
        p = list(
            jsonpath.query(
                "$.parameter[?@name == 'designation'].part[?@valueCoding.code == '900000000000003001']",
                json,
            ).pointers()  # noqa
        )[0]

        return next(
            filter(lambda x: x["name"] == "value", p.resolve_parent(json)[0])
        )["valueString"]  # noqa

    def _sctid_is_inactive(self, json: Dict) -> bool:
        """Vérifie si le concept est inactif
        args:
            json: Résultat de l'opération lookup
        returns:
            True si le concept est inactif, False sinon
        """
        p = list(
            jsonpath.query(
                "$.parameter[?@name == 'property'].part[?@valueCode == 'inactive']",
                json,
            ).pointers()  # noqa
        )[0]

        is_inactive = next(
            filter(lambda x: x["name"] == "value", p.resolve_parent(json)[0])
        )["valueBoolean"]

        return is_inactive
    
    def get_status(self, sctid: str) -> int | None:
        """Donne le statut du concept `sctid`
        args:
            sctid: SCTID du concept
        returns:
            Statut du concept `sctid` :
                - 1 : actif
                - 0 : inactif
                - None : concept non trouvé
        """
        if self.cache is not None:
            if sctid in self.cache["conceptId"].values:
                return ACTIVE_STATUS
            
        json = self.lookup(sctid)
        
        if self._sctid_is_inactive(json):
            return INACTIVE_STATUS
        else:
            return ACTIVE_STATUS