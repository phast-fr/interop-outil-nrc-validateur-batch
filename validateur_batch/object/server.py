import logging
import hashlib
import json
import jsonpath
import requests
from pathlib import Path
from typing import Dict, List
from validateur_batch.object.sctrf2 import SctEd

logger = logging.getLogger(__name__)


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
        international: SctEd = None,
        cache_dir: str = "cache",
    ):
        """
        Args:
            endpoint: Endpoint de votre serveur de Terminologies FHIR
            cache_file: Fichier de cache pour les données récupérées du FTS (si vide, le FTS est utilisé pour chaque requête)
        """
        self.endpoint = endpoint
        self.login = login
        self.password = password
        self.international = international
        self.session = requests.Session()
        self._available_versions: List[str] | None = None
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        if versioning:
            self.lookup_base_url = f"{endpoint}/CodeSystem/$lookup?system=http://snomed.info/sct&version=http://snomed.info/sct/900000000000207008"  # noqa

        else:
            self.lookup_base_url = (
                f"{endpoint}/CodeSystem/$lookup?system=http://snomed.info/sct"  # noqa
            )

        logger.info(f"Version SNOMED CT utilisée sur le serveur FTS : {self.last_available_version()}")

    def available_versions(self) -> List[str]:
        """Renvoie la liste des versions disponibles sur le serveur FTS

        Returns:
            Liste des versions disponibles
        """
        if self._available_versions is not None:
            return self._available_versions

        auth = (self.login, self.password) if self.login and self.password else None

        url = f"{self.endpoint}/metadata?mode=terminology"
        response = self.session.request("GET", url, auth=auth)
        response.raise_for_status()

        versions = list(jsonpath.findall('$codeSystem[?(@.uri=="http://snomed.info/sct")].version[*].code', response.json())) # noqa

        if not versions:
            # Repli : certains serveurs (ex. Snowstorm) n'implémentent pas
            # TerminologyCapabilities et ignorent `mode=terminology`, on
            # récupère alors les versions via une recherche de CodeSystem.
            logger.info("Aucune version trouvée via /metadata?mode=terminology, repli sur une recherche CodeSystem.")
            url = f"{self.endpoint}/CodeSystem"
            response = self.session.request("GET", url, params={"url": "http://snomed.info/sct"}, auth=auth)
            response.raise_for_status()
            versions = sorted(jsonpath.findall('$entry[*].resource.version', response.json())) # noqa

        self._available_versions = versions

        return self._available_versions

    def last_available_version(self) -> str:
        """Renvoie la dernière version disponible sur le serveur FTS

        Returns:
            Dernière version disponible
        """
        versions = self.available_versions()
        if len(versions) == 0:
            raise ValueError("Aucune version de SNOMED CT trouvée sur le serveur FTS.")
        return versions[-1]

    def ecl(self, ecl: str) -> List[str]:
        """Envoie une requête ECL au FTS

        Args:
            ecl: Requête ECL

        Returns:
            Liste des SCTID correspondant à la requête ECL
        """
        cache_key = hashlib.sha256(ecl.encode()).hexdigest()
        cache_file = self._cache_dir / f"{cache_key}.json"
        current_version = self.last_available_version()

        if cache_file.exists():
            cached = json.loads(cache_file.read_text())
            if cached.get("version_uri") == current_version:
                logger.info(f"Utilisation du cache pour la requête ECL: {ecl}")
                return cached["codes"]
            else:
                logger.info(f"Version du cache ({cached.get('version_uri')}) différente de la version actuelle du serveur FTS ({current_version}). Requête ECL envoyée au serveur.")

        url = f"{self.endpoint}/ValueSet/$expand"
        offset = 0
        codes = []
        version_uri = None
        while True:
            body = {
                "resourceType": "Parameters",
                "parameter": [
                    {
                        "name": "valueSet",
                        "resource": {
                            "resourceType": "ValueSet",
                            "compose": {
                                "include": [
                                    {
                                        "system": "http://snomed.info/sct",
                                        "filter": [
                                            {"property": "constraint", "op": "=", "value": ecl}
                                        ],
                                    }
                                ]
                            },
                        },
                    },
                    {"name": "offset", "valueInteger": offset},
                ],
            }
            # La recherche ECL passe en POST (plutôt qu'un $expand?url=...fhir_vs=ecl/...
            # en GET) car certains serveurs FTS (ex. Ontoserver) interprètent mal le "|"
            # délimitant les libellés de termes dans les expressions ECL une fois inséré
            # dans une URL, même correctement encodé.
            response = self.session.request(
                "POST",
                url,
                json=body,
                headers={"Content-Type": "application/fhir+json"},
                auth=(self.login, self.password)
                if self.login and self.password
                else None,
            )
            response.raise_for_status()
            total = jsonpath.match(
                "$.expansion.total",
                response.text,
            ).obj
            page_codes = jsonpath.findall(
                "$.expansion.contains[*].code",
                response.text,
            )
            version_param_match = jsonpath.match(
                "$.expansion.parameter[?@name == 'version']",
                response.text,
            )
            version_param = version_param_match.obj if version_param_match else None
            # value[x] est polymorphe en FHIR : selon le serveur, le paramètre
            # "version" est porté par valueUri, valueString ou valueCode.
            raw_version_uri = (
                version_param.get("valueUri")
                or version_param.get("valueString")
                or version_param.get("valueCode")
            ) if version_param else None
            version_uri = raw_version_uri.split("|")[-1] if raw_version_uri else None
            codes.extend(page_codes)
            if len(codes) < total:
                offset = len(codes)
            else:
                break

        cache_file.write_text(
            json.dumps({"ecl": ecl, "version_uri": version_uri, "codes": codes})
        )
        return codes


    def _sctid_is_inactive(self, data: Dict) -> bool:
        """Vérifie si le concept est inactif

        args:
            data: Résultat de l'opération lookup

        returns:
            True si le concept est inactif, False sinon
        """
        p = list(
            jsonpath.query(
                "$.parameter[?@name == 'property'].part[?@valueCode == 'inactive']",
                data,
            ).pointers()  # noqa
        )[0]

        is_inactive = next(
            filter(lambda x: x["name"] == "value", p.resolve_parent(data)[0])
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
        if self.international:
            if self.international.is_active(sctid):
                return ACTIVE_STATUS
            else:
                return INACTIVE_STATUS

        data = self.lookup(sctid)
        if self._sctid_is_inactive(data):
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

        fsn = None

        if self.international:
            try:
                fsn = self.international.get_fsn(sctid)
            except KeyError:
                logger.warning(f"Concept {sctid} non trouvé dans les RF2 de l'édition internationale. Requête envoyée au serveur FTS pour obtenir le FSN.")
                fsn = None

        if fsn is None:
            data = self.lookup(sctid)
            p = list(
                jsonpath.query(
                    "$.parameter[?@name == 'designation'].part[?@valueCoding.code == '900000000000003001']",
                    data,
                ).pointers()  # noqa
            )[0]
            fsn = next(
                filter(lambda x: x["name"] == "value", p.resolve_parent(data)[0])
            )["valueString"]  # noqa

        return fsn
    
    def get_pten(self, sctid: str) -> str:
        """Donne le PTEN du concept `sctid`

        args:
            sctid: SCTID du concept

        returns:
            PTEN du concept
        """
        if self.international:
            try:
                pten = self.international.get_pten(sctid)
            except KeyError:
                logger.warning(f"Concept {sctid} non trouvé dans les RF2 de l'édition internationale.")
                pten = ""
        else:
            pten = ""
        return pten

