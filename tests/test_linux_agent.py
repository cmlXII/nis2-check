
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from agents.linux import collector


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


def test_agent_linux_produit_un_resultat_conforme(monkeypatch):
    monkeypatch.setattr(
        collector.platform, "system", lambda: "Linux"
    )
    monkeypatch.setattr(
        collector.platform, "node", lambda: "test-linux"
    )
    monkeypatch.setattr(
        collector.platform,
        "freedesktop_os_release",
        lambda: {"PRETTY_NAME": "Debian 12"}
    )

    monkeypatch.setattr(
        collector,
        "controle_ssh",
        lambda: ("ssh", "ok", "Configuration SSH correcte")
    )
    monkeypatch.setattr(
        collector,
        "controle_ports",
        lambda: ("ports", "ok", "Aucun problème détecté")
    )
    monkeypatch.setattr(
        collector,
        "controle_pare_feu",
        lambda: ("pare-feu", "attention", "Vérification nécessaire")
    )
    monkeypatch.setattr(
        collector,
        "controle_mises_a_jour",
        lambda: ("mises à jour", "ok", "Système à jour")
    )

    resultat = collector.collecter()

    VALIDATEUR.validate(resultat)

    assert resultat["asset"]["platform"] == "linux"
    assert resultat["asset"]["hostname"] == "test-linux"
    assert len(resultat["checks"]) == 4


def test_agent_linux_refuse_windows(monkeypatch):
    monkeypatch.setattr(
        collector.platform, "system", lambda: "Windows"
    )

    with pytest.raises(RuntimeError):
        collector.collecter()


def test_conversion_statut_ignore():
    controle = (
        "pare-feu",
        "ignoré",
        "Droits administrateur requis"
    )

    resultat = collector.convertir_controle(controle)

    assert resultat["status"] == "ignore"
    assert resultat["severity"] == "low"


def test_conversion_refuse_controle_inconnu():
    controle = (
        "controle-inconnu",
        "ok",
        "Test"
    )

    with pytest.raises(ValueError):
        collector.convertir_controle(controle)
