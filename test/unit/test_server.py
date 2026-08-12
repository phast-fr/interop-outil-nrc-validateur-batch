import json
from unittest.mock import Mock, patch

import pytest

from validateur_batch.object.server import Server


@pytest.mark.parametrize(
    ("parameters", "expected_version"),
    [
        (
            [{"name": "version", "valueString": "http://snomed.info/sct|20260701"}],
            "20260701",
        ),
        ([], None),
    ],
)
def test_ecl_caches_response_version_or_metadata_fallback(
    tmp_path, parameters, expected_version
):
    current_version = "http://snomed.info/sct/11000315107/version/20260621"
    response = Mock()
    response.text = json.dumps(
        {
            "resourceType": "ValueSet",
            "expansion": {
                "total": 1,
                "parameter": parameters,
                "contains": [{"system": "http://snomed.info/sct", "code": "123"}],
            },
        }
    )
    response.raise_for_status.return_value = None

    fts = object.__new__(Server)
    fts.endpoint = "https://example.test/fhir"
    fts.login = None
    fts.password = None
    fts.session = Mock()
    fts.session.request.return_value = response
    fts._cache_dir = tmp_path
    fts._sct_version = None
    fts.last_available_version = Mock(return_value=current_version)

    assert fts.ecl("<< 123") == ["123"]

    cache_files = list(tmp_path.glob("*.json"))
    assert len(cache_files) == 1
    assert json.loads(cache_files[0].read_text())["version_uri"] == expected_version


def test_ecl_includes_pinned_version_in_request_body(tmp_path):
    """Quand une version est figée, elle doit être portée par le "include" de
    la requête POST envoyée au serveur, et last_available_version() ne doit
    pas être appelée (pas de round-trip réseau superflu)."""
    pinned = "http://snomed.info/sct/900000000000207008/version/20260801"
    response = Mock()
    response.text = json.dumps(
        {
            "resourceType": "ValueSet",
            "expansion": {
                "total": 1,
                "parameter": [],
                "contains": [{"system": "http://snomed.info/sct", "code": "123"}],
            },
        }
    )
    response.raise_for_status.return_value = None

    fts = object.__new__(Server)
    fts.endpoint = "https://example.test/fhir"
    fts.login = None
    fts.password = None
    fts.session = Mock()
    fts.session.request.return_value = response
    fts._cache_dir = tmp_path
    fts._sct_version = pinned
    fts.last_available_version = Mock(
        side_effect=AssertionError("ne doit pas être appelé quand la version est figée")
    )

    assert fts.ecl("<< 123") == ["123"]

    _, kwargs = fts.session.request.call_args
    include = kwargs["json"]["parameter"][0]["resource"]["compose"]["include"][0]
    assert include["version"] == pinned


def test_init_builds_pinned_version_lookup_url(tmp_path):
    pinned = "http://snomed.info/sct/900000000000207008/version/20260801"

    with patch("validateur_batch.object.server.requests.Session"):
        fts = Server(
            "https://example.test/fhir",
            cache_dir=str(tmp_path),
            sct_version=pinned,
        )

    assert fts.lookup_base_url == (
        f"https://example.test/fhir/CodeSystem/$lookup?system=http://snomed.info/sct&version={pinned}"
    )
    assert fts._sct_version == pinned


def test_init_with_pinned_version_does_not_call_server(tmp_path):
    """Figer la version évite l'appel réseau à /metadata au démarrage."""
    with patch("validateur_batch.object.server.requests.Session") as session_cls:
        session = session_cls.return_value
        fts = Server(
            "https://example.test/fhir",
            cache_dir=str(tmp_path),
            sct_version="http://snomed.info/sct/900000000000207008/version/20260801",
        )

    session.request.assert_not_called()
    assert fts._sct_version == "http://snomed.info/sct/900000000000207008/version/20260801"
