
import json
import os
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
COLLECTOR = ROOT / "agents" / "windows" / "collector.ps1"
SCHEMA_PATH = ROOT / "schemas" / "agent-result.schema.json"


with SCHEMA_PATH.open(encoding="utf-8") as fichier:
    SCHEMA = json.load(fichier)

VALIDATEUR = Draft202012Validator(
    SCHEMA,
    format_checker=FormatChecker()
)


def lire_collecteur():
    return COLLECTOR.read_text(encoding="utf-8")


def test_collecteur_windows_existe():
    assert COLLECTOR.is_file()


def test_syntaxe_powershell_valide():
    commande = r"""
    $tokens = $null
    $errors = $null

    [System.Management.Automation.Language.Parser]::ParseFile(
        $env:NIS2_COLLECTOR_PATH,
        [ref]$tokens,
        [ref]$errors
    ) | Out-Null

    if ($errors.Count -gt 0) {
        $errors | ForEach-Object { Write-Error $_.Message }
        exit 1
    }
    """

    environnement = os.environ.copy()
    environnement["NIS2_COLLECTOR_PATH"] = str(COLLECTOR)

    resultat = subprocess.run(
        ["pwsh", "-NoProfile", "-Command", commande],
        capture_output=True,
        text=True,
        env=environnement
    )

    assert resultat.returncode == 0, resultat.stderr


def test_identifiants_controles_windows():
    contenu = lire_collecteur()

    identifiants = [
        "FIREWALL-001",
        "NETWORK-PORTS-001",
        "UPDATES-001",
    ]

    for identifiant in identifiants:
        assert identifiant in contenu


def test_statuts_compatibles_avec_le_schema():
    statuts_autorises = set(
        SCHEMA["properties"]["checks"]["items"]
        ["properties"]["status"]["enum"]
    )

    contenu = lire_collecteur()

    for statut in ["ok", "attention", "non_verifie"]:
        assert statut in statuts_autorises
        assert f'"{statut}"' in contenu


def test_structure_json_windows_compatible():
    contenu = lire_collecteur()

    champs_attendus = [
        "schema_version",
        "asset",
        "asset_id",
        "hostname",
        "platform",
        "os_version",
        "agent",
        "version",
        "collected_at",
        "checks",
        "control_id",
        "status",
        "severity",
        "message",
        "evidence",
        "observed_value",
        "source",
    ]

    for champ in champs_attendus:
        assert champ in contenu
