
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


RACINE_PROJET = Path(__file__).resolve().parents[1]

SCHEMA_PAR_DEFAUT = (
    RACINE_PROJET / "schemas" / "agent-result.schema.json"
)


def charger_schema(chemin_schema=None):
    chemin = Path(chemin_schema or SCHEMA_PAR_DEFAUT)

    try:
        with chemin.open(encoding="utf-8") as fichier:
            schema = json.load(fichier)
    except FileNotFoundError as erreur:
        raise ValueError(
            f"Schéma introuvable : {chemin}"
        ) from erreur
    except json.JSONDecodeError as erreur:
        raise ValueError(
            f"Le schéma JSON est invalide : {erreur}"
        ) from erreur

    Draft202012Validator.check_schema(schema)

    return schema


def valider_resultat_agent(resultat, chemin_schema=None):
    if not isinstance(resultat, dict):
        raise ValueError(
            "Le résultat de l'agent doit être un objet JSON."
        )

    schema = charger_schema(chemin_schema)

    validateur = Draft202012Validator(
        schema,
        format_checker=FormatChecker()
    )

    erreurs = sorted(
        validateur.iter_errors(resultat),
        key=lambda erreur: list(
            map(str, erreur.absolute_path)
        )
    )

    if erreurs:
        details = []

        for erreur in erreurs:
            emplacement = ".".join(
                map(str, erreur.absolute_path)
            ) or "racine"

            details.append(
                f"{emplacement} : {erreur.message}"
            )

        raise ValueError(
            "Résultat de l'agent invalide :\n- "
            + "\n- ".join(details)
        )

    return resultat


def charger_resultat_agent(chemin_json, chemin_schema=None):
    chemin = Path(chemin_json)

    try:
        with chemin.open(encoding="utf-8") as fichier:
            resultat = json.load(fichier)

    except FileNotFoundError as erreur:
        raise ValueError(
            f"Fichier de résultat introuvable : {chemin}"
        ) from erreur

    except json.JSONDecodeError as erreur:
        raise ValueError(
            f"Le fichier JSON est invalide : {erreur}"
        ) from erreur

    except OSError as erreur:
        raise ValueError(
            f"Impossible de lire le fichier : {erreur}"
        ) from erreur

    return valider_resultat_agent(
        resultat,
        chemin_schema
    )
