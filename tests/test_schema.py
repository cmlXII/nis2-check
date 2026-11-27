
import json
from pathlib import Path

import pytest
from jsonschema import (
    Draft202012Validator,
    FormatChecker,
    ValidationError
)


SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "schemas"
    / "agent-result.schema.json"
)

with SCHEMA_PATH.open(encoding="utf-8") as fichier:
    SCHEMA = json.load(fichier)

VALIDATEUR = Draft202012Validator(
    SCHEMA,
    format_checker=FormatChecker()
)


def resultat_valide(platform):
    return {
        "schema_version": "1.0",
        "asset": {
            "asset_id": "MACHINE-001",
            "hostname": "machine-test",
            "platform": platform,
            "os_version": "Version de test"
        },
        "agent": {
            "version": "0.1.0"
        },
        "collected_at": "2026-11-27T08:00:00Z",
        "checks": [
            {
                "control_id": "FIREWALL-001",
                "status": "attention",
                "severity": "high",
                "message": "Le pare-feu nécessite une vérification.",
                "evidence": {
                    "observed_value": "INPUT ACCEPT",
                    "source": "firewall"
                }
            }
        ]
    }


def test_schema_valide():
    Draft202012Validator.check_schema(SCHEMA)


@pytest.mark.parametrize("platform", ["linux", "windows"])
def test_resultat_valide(platform):
    resultat = resultat_valide(platform)
    VALIDATEUR.validate(resultat)


def test_statut_inconnu_refuse():
    resultat = resultat_valide("linux")
    resultat["checks"][0]["status"] = "inconnu"

    with pytest.raises(ValidationError):
        VALIDATEUR.validate(resultat)


def test_plateforme_inconnue_refuse():
    resultat = resultat_valide("linux")
    resultat["asset"]["platform"] = "macos"

    with pytest.raises(ValidationError):
        VALIDATEUR.validate(resultat)


def test_champ_obligatoire_manquant_refuse():
    resultat = resultat_valide("linux")
    del resultat["collected_at"]

    with pytest.raises(ValidationError):
        VALIDATEUR.validate(resultat)


def test_date_invalide_refuse():
    resultat = resultat_valide("linux")
    resultat["collected_at"] = "pas-une-date"

    with pytest.raises(ValidationError):
        VALIDATEUR.validate(resultat)
