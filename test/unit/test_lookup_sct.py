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
US_ENGLISH_REFSET = "900000000000509007"


def _desc_row(desc_id, concept_id, term, type_id, case_sig=CASE_INSENSITIVE, active="1"):
    return f"{desc_id}\t20260621\t{active}\t11000315107\t{concept_id}\tfr\t{type_id}\t{term}\t{case_sig}\n"


def _lang_row(desc_id, acceptability, active="1"):
    return f"lang-{desc_id}\t20260621\t{active}\t11000315107\t999\t{desc_id}\t{acceptability}\n"


def _en_lang_row(desc_id, acceptability, active="1"):
    return f"en-{desc_id}\t20260621\t{active}\t900000000000207008\t{US_ENGLISH_REFSET}\t{desc_id}\t{acceptability}\n"


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

    en_rows = [
        _desc_row("300", "10", "Kidney structure (body structure)", FSN_TYPE),
        _desc_row("301", "10", "Kidney structure", SYNONYM_TYPE),
        _desc_row("302", "10", "Old kidney term", SYNONYM_TYPE),
    ]
    (
        snapshot / "Terminology" / "sct2_Description_Snapshot-en_FR1000315_20260621.txt"
    ).write_text(DESC_HEADER + "".join(en_rows), encoding="utf-8")
    en_lang_rows = [
        _en_lang_row("300", PREFERRED),
        _en_lang_row("301", PREFERRED),
        _en_lang_row("302", PREFERRED, active="0"),
    ]
    (
        snapshot
        / "Refset"
        / "Language"
        / "der2_cRefset_LanguageSnapshot-en_FR1000315_20260621.txt"
    ).write_text(LANG_HEADER + "".join(en_lang_rows), encoding="utf-8")

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
    assert kidney["English FSN (Int. Edition )"] == "Kidney structure (body structure)"
    assert kidney["DESCRIPTION ID du FSN anglais"] == "300"
    assert kidney["Case significance FSN ang"] == CASE_INSENSITIVE
    assert kidney["English preferred Term(Int. Edition )"] == "Kidney structure"
    assert kidney["DESCRIPTION ID du PT anglais"] == "301"
    assert kidney["Case significance PT ang"] == CASE_INSENSITIVE
    assert kidney["Terme Préféré Français"] == "rein actif"
    assert kidney["DESCRIPTION ID du terme préféré français"] == "104"
    assert kidney["Case significance PT français"] == CASE_INSENSITIVE
    assert kidney["FSN Français"] == ""

    # Synonymes acceptables triés par Description ID croissant : 100, 102, 103
    assert kidney["Synonyme Acceptable FR 1"] == "structure entière du rein"
    assert kidney["DESCRIPTION ID du synonyme 1 acceptable français"] == "100"
    assert (
        kidney["Case significance SYNONYME ACCEPTABLE 1 français"]
        == CASE_INSENSITIVE
    )
    assert kidney["Synonyme Acceptable FR 2"] == "rognon"
    assert kidney["DESCRIPTION ID du synonyme 2 acceptable français"] == "102"
    assert kidney["Synonyme Acceptable FR 3"] == "structure du rein"
    assert kidney["DESCRIPTION ID du synonyme 3 acceptable français"] == "103"
    assert kidney["Synonyme Acceptable FR 4"] == ""

    # Concept 20 n'a que des descriptions inactives : tout reste vide côté français.
    inactive = result.loc[result["SCTID du concept"] == "20"].iloc[0]
    assert inactive["Terme Préféré Français"] == ""


@pytest.fixture
def international_rf2(tmp_path: Path) -> Path:
    """RF2 international autonome, avec un concept absent du RF2 français."""
    root = tmp_path / "International"
    (root / "Snapshot" / "Terminology").mkdir(parents=True)
    (root / "Snapshot" / "Refset" / "Language").mkdir(parents=True)

    (root / "release_package_information.json").write_text(
        '{"effectiveTime": "20260801"}', encoding="utf-8"
    )

    en_rows = [
        _desc_row("900", "30", "Renal tubular epithelium (body structure)", FSN_TYPE),
        _desc_row("901", "30", "Renal tubular epithelium", SYNONYM_TYPE),
    ]
    (
        root / "Snapshot" / "Terminology" / "sct2_Description_Snapshot-en_INT_20260801.txt"
    ).write_text(DESC_HEADER + "".join(en_rows), encoding="utf-8")

    en_lang_rows = [
        _en_lang_row("900", PREFERRED),
        _en_lang_row("901", PREFERRED),
    ]
    (
        root
        / "Snapshot"
        / "Refset"
        / "Language"
        / "der2_cRefset_LanguageSnapshot-en_INT_20260801.txt"
    ).write_text(LANG_HEADER + "".join(en_lang_rows), encoding="utf-8")

    return root


def test_build_lookup_sct_falls_back_to_international_rf2(
    tmp_path: Path, rf2_snapshot: Path, international_rf2: Path
):
    """Concept trop récent pour le RF2 FR : repli sur le RF2 international."""
    scope_csv = tmp_path / "scope_concepts.csv"
    scope_csv.write_text(
        "section;conceptId;fsn;pten\n"
        "kidney;30;Structure of renal tubular epithelium (body structure);Renal tubular epithelium\n",
        encoding="utf-8",
    )

    output_csv = tmp_path / "lookup_sct.csv"
    build_lookup_sct(
        str(scope_csv),
        str(rf2_snapshot),
        "20260621",
        str(output_csv),
        international=str(international_rf2),
    )

    result = pd.read_csv(output_csv, sep=";", dtype=str, na_filter=False)
    concept = result.loc[result["SCTID du concept"] == "30"].iloc[0]
    assert concept["English FSN (Int. Edition )"] == "Renal tubular epithelium (body structure)"
    assert concept["DESCRIPTION ID du FSN anglais"] == "900"
    assert concept["English preferred Term(Int. Edition )"] == "Renal tubular epithelium"
    assert concept["DESCRIPTION ID du PT anglais"] == "901"
    # Toujours pas de traduction française : le concept n'existe pas encore
    # dans le RF2 français, donc aucune traduction ne peut exister.
    assert concept["Terme Préféré Français"] == ""


def test_build_lookup_sct_without_international_leaves_columns_empty(
    tmp_path: Path, rf2_snapshot: Path
):
    """Sans --international, un concept trop récent reste sans Description ID."""
    scope_csv = tmp_path / "scope_concepts.csv"
    scope_csv.write_text(
        "section;conceptId;fsn;pten\n"
        "kidney;30;Structure of renal tubular epithelium (body structure);Renal tubular epithelium\n",
        encoding="utf-8",
    )

    output_csv = tmp_path / "lookup_sct.csv"
    build_lookup_sct(str(scope_csv), str(rf2_snapshot), "20260621", str(output_csv))

    result = pd.read_csv(output_csv, sep=";", dtype=str, na_filter=False)
    concept = result.loc[result["SCTID du concept"] == "30"].iloc[0]
    assert concept["English FSN (Int. Edition )"] == "Structure of renal tubular epithelium (body structure)"
    assert concept["DESCRIPTION ID du FSN anglais"] == ""
