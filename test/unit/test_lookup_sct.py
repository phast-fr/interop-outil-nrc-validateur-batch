from pathlib import Path

import pandas as pd
import pytest

from validateur_batch.lookup_sct import build_lookup_sct


DESC_HEADER = "id\teffectiveTime\tactive\tmoduleId\tconceptId\tlanguageCode\ttypeId\tterm\tcaseSignificanceId\n"
LANG_HEADER = "id\teffectiveTime\tactive\tmoduleId\trefsetId\treferencedComponentId\tacceptabilityId\n"

FSN_TYPE = "900000000000003001"
SYNONYM_TYPE = "900000000000013009"
PREFERRED = "900000000000548007"
ACCEPTABLE = "900000000000549004"
CASE_INSENSITIVE = "900000000000448009"


def _desc_row(desc_id, concept_id, term, type_id, case_sig=CASE_INSENSITIVE, active="1"):
    return f"{desc_id}\t20260621\t{active}\t11000315107\t{concept_id}\tfr\t{type_id}\t{term}\t{case_sig}\n"


def _lang_row(desc_id, acceptability, active="1"):
    return f"lang-{desc_id}\t20260621\t{active}\t11000315107\t999\t{desc_id}\t{acceptability}\n"


@pytest.fixture
def rf2_snapshot(tmp_path: Path) -> Path:
    snapshot = tmp_path / "Snapshot"
    (snapshot / "Terminology").mkdir(parents=True)
    (snapshot / "Refset" / "Language").mkdir(parents=True)

    desc_rows = [
        _desc_row("100", "10", "structure entière du rein", SYNONYM_TYPE),
        _desc_row("101", "10", "rein", SYNONYM_TYPE),
        _desc_row("103", "10", "structure du rein", SYNONYM_TYPE),
        _desc_row("102", "10", "rognon", SYNONYM_TYPE),
        _desc_row("104", "10", "rein actif", SYNONYM_TYPE),
        _desc_row("200", "20", "inactive term", SYNONYM_TYPE, active="0"),
    ]
    (snapshot / "Terminology" / "sct2_Description_Snapshot-fr_FR1000315_20260621.txt").write_text(
        DESC_HEADER + "".join(desc_rows), encoding="utf-8"
    )

    lang_rows = [
        _lang_row("100", ACCEPTABLE),
        _lang_row("101", PREFERRED, active="0"),
        _lang_row("102", ACCEPTABLE),
        _lang_row("103", ACCEPTABLE),
        _lang_row("104", PREFERRED),
        _lang_row("200", PREFERRED),
    ]
    (
        snapshot
        / "Refset"
        / "Language"
        / "der2_cRefset_LanguageSnapshot-fr_FR1000315_20260621.txt"
    ).write_text(LANG_HEADER + "".join(lang_rows), encoding="utf-8")

    return snapshot


def test_build_lookup_sct(tmp_path: Path, rf2_snapshot: Path):
    scope_csv = tmp_path / "scope_concepts.csv"
    scope_csv.write_text(
        "section;conceptId;fsn;pten\n"
        "kidney;10;Structure of kidney (body structure);Kidney\n"
        "kidney;20;Structure of inactive concept (body structure);Inactive\n",
        encoding="utf-8",
    )

    output_csv = tmp_path / "lookup_sct.csv"
    build_lookup_sct(str(scope_csv), str(rf2_snapshot), "20260621", str(output_csv))

    result = pd.read_csv(output_csv, sep=";", dtype=str, na_filter=False)
    assert len(result) == 2

    kidney = result.loc[result["SCTID du concept"] == "10"].iloc[0]
    assert kidney["English FSN (Int. Edition )"] == "Structure of kidney (body structure)"
    assert kidney["Terme Préféré Français"] == "rein actif"
    assert kidney["DESCRIPTION ID du terme préféré français"] == "104"
    assert kidney["FSN Français"] == ""

    # Synonymes acceptables triés par Description ID croissant : 100, 102, 103
    assert kidney["Synonyme Acceptable FR 1"] == "structure entière du rein"
    assert kidney["DESCRIPTION ID du synonyme 1 acceptable français"] == "100"
    assert kidney["Synonyme Acceptable FR 2"] == "rognon"
    assert kidney["DESCRIPTION ID du synonyme 2 acceptable français"] == "102"
    assert kidney["Synonyme Acceptable FR 3"] == "structure du rein"
    assert kidney["DESCRIPTION ID du synonyme 3 acceptable français"] == "103"
    assert kidney["Synonyme Acceptable FR 4"] == ""

    # Concept 20 n'a que des descriptions inactives : tout reste vide côté français.
    inactive = result.loc[result["SCTID du concept"] == "20"].iloc[0]
    assert inactive["Terme Préféré Français"] == ""
