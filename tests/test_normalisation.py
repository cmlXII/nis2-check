
import json
import pytest

from nis2check.normalisation import (
    valider_resultat_agent,
    charger_resultat_agent,
)


def resultat_valide():
    return {
        "schema_version": "1.0",
        "asset": {
            "asset_id": "MACHINE-001",
            "hostname": "machine-test",
            "platform": "linux",
            "os_version": "Kali Linux"
        },
        "agent": {
            "version": "0.1.0"
        },
        "collected_at": "2026-11-27T09:00:00Z",
        "checks": [
            {
                "control_id": "FIREWALL-001",
                "status": "ok",
                "severity": "low",
                "message": "Pare-feu actif",
                "evidence": {
                    "observed_value": "active",
                    "source": "test"
                }
            }
        ]
    }


@pytest.mark.parametrize("platform", ["linux", "windows"])
def test_validation_resultat_linux_windows(platform):
    resultat = resultat_valide()
    resultat["asset"]["platform"] = platform

    assert valider_resultat_agent(resultat) == resultat


def test_refus_statut_inconnu():
    resultat = resultat_valide()
    resultat["checks"][0]["status"] = "inconnu"

    with pytest.raises(ValueError):
        valider_resultat_agent(resultat)


def test_refus_champ_obligatoire_manquant():
    resultat = resultat_valide()
    del resultat["collected_at"]

    with pytest.raises(ValueError):
        valider_resultat_agent(resultat)


def test_chargement_fichier_json(tmp_path):
    resultat = resultat_valide()
    fichier = tmp_path / "resultat.json"

    fichier.write_text(
        json.dumps(resultat),
        encoding="utf-8"
    )

    assert charger_resultat_agent(fichier) == resultat


def test_refus_json_invalide(tmp_path):
    fichier = tmp_path / "resultat.json"
    fichier.write_text("{json invalide", encoding="utf-8")

    with pytest.raises(ValueError):
        charger_resultat_agent(fichier)


def test_refus_fichier_introuvable():
    with pytest.raises(ValueError):
        charger_resultat_agent("fichier_inexistant.json")
