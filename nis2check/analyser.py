
import argparse
import json
import sys

from nis2check.normalisation import charger_resultat_agent
from nis2check.analyse_agents import analyser_agent


def main():
    parser = argparse.ArgumentParser(
        description="Analyse un résultat technique NIS2-Check."
    )

    parser.add_argument(
        "fichier",
        help="Chemin du fichier JSON produit par un agent."
    )

    args = parser.parse_args()

    try:
        resultat = charger_resultat_agent(args.fichier)
        analyse = analyser_agent(resultat)

        print(
            json.dumps(
                analyse,
                indent=2,
                ensure_ascii=False
            )
        )

    except ValueError as erreur:
        print(f"ERREUR : {erreur}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
