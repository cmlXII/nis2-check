
import json
import platform
from datetime import datetime, timezone

from nis2check.controles import (
    controle_ssh,
    controle_ports,
    controle_pare_feu,
    controle_mises_a_jour,
)


AGENT_VERSION = "0.1.0"

IDENTIFIANTS_CONTROLES = {
    "ssh": "SSH-001",
    "ports": "NETWORK-PORTS-001",
    "pare-feu": "FIREWALL-001",
    "mises à jour": "UPDATES-001",
}

STATUTS = {
    "ok": "ok",
    "échec": "echec",
    "echec": "echec",
    "attention": "attention",
    "non vérifié": "non_verifie",
    "non_verifie": "non_verifie",
    "ignoré": "ignore",
    "ignore": "ignore",
    "non applicable": "non_applicable",
    "non_applicable": "non_applicable",
}

GRAVITES = {
    "SSH-001": "high",
    "NETWORK-PORTS-001": "medium",
    "FIREWALL-001": "high",
    "UPDATES-001": "medium",
}


def obtenir_version_linux():
    """Récupère le nom et la version de la distribution Linux."""
    try:
        informations = platform.freedesktop_os_release()
        nom = informations.get("PRETTY_NAME", platform.system())
        return nom
    except (OSError, AttributeError):
        return platform.system()


def convertir_controle(controle):
    """Transforme un contrôle existant au format commun JSON."""
    nom, statut, message = controle

    if nom not in IDENTIFIANTS_CONTROLES:
        raise ValueError(f"Contrôle inconnu : {nom}")

    control_id = IDENTIFIANTS_CONTROLES[nom]

    if statut not in STATUTS:
        raise ValueError(f"Statut inconnu : {statut}")

    statut_normalise = STATUTS[statut]

    severite = (
        "low"
        if statut_normalise in ("ok", "ignore", "non_applicable")
        else GRAVITES[control_id]
    )

    return {
        "control_id": control_id,
        "status": statut_normalise,
        "severity": severite,
        "message": message,
        "evidence": {
            "observed_value": message,
            "source": "nis2check.controles"
        }
    }


def collecter():
    """Collecte les informations techniques de la machine Linux."""

    if platform.system().lower() != "linux":
        raise RuntimeError("Cet agent est réservé aux systèmes Linux.")

    hostname = platform.node()

    controles = [
        controle_ssh(),
        controle_ports(),
        controle_pare_feu(),
        controle_mises_a_jour(),
    ]

    resultat = {
        "schema_version": "1.0",
        "asset": {
            "asset_id": hostname,
            "hostname": hostname,
            "platform": "linux",
            "os_version": obtenir_version_linux(),
        },
        "agent": {
            "version": AGENT_VERSION,
        },
        "collected_at": datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        ).replace("+00:00", "Z"),
        "checks": [
            convertir_controle(controle)
            for controle in controles
        ],
    }

    return resultat


def main():
    """Exécute la collecte et affiche le résultat JSON."""
    resultat = collecter()
    print(json.dumps(resultat, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
