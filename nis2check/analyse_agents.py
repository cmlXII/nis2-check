
from collections import Counter

from nis2check.normalisation import valider_resultat_agent


STATUTS_EVALUES = {"ok", "echec", "attention"}

STATUTS_EXCLUS_COUVERTURE = {"ignore", "non_applicable"}

SEVERITES = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def analyser_agent(resultat):
    valider_resultat_agent(resultat)

    checks = resultat["checks"]

    compteur_statuts = Counter(
        check["status"] for check in checks
    )

    compteur_severites = Counter(
        check["severity"] for check in checks
    )

    controles_evalues = [
        check for check in checks
        if check["status"] in STATUTS_EVALUES
    ]

    actions_correctives = [
        check for check in checks
        if check["status"] in {"echec", "attention"}
    ]

    actions_verification = [
        check for check in checks
        if check["status"] == "non_verifie"
    ]

    def trier_actions(actions):
        return sorted(
            actions,
            key=lambda check: (
                -SEVERITES[check["severity"]],
                check["control_id"]
            )
        )

    total = len(checks)
    reussis = compteur_statuts["ok"]
    nombre_evalues = len(controles_evalues)

    nombre_exclus = sum(
        compteur_statuts[statut]
        for statut in STATUTS_EXCLUS_COUVERTURE
    )

    nombre_applicables = total - nombre_exclus

    score = (
        round(reussis / nombre_evalues * 100)
        if nombre_evalues > 0 else None
    )

    couverture = (
        round(nombre_evalues / nombre_applicables * 100)
        if nombre_applicables > 0 else None
    )

    controles_en_echec = compteur_statuts["echec"]
    controles_en_attention = compteur_statuts["attention"]
    controles_non_verifies = compteur_statuts["non_verifie"]

    return {
        "asset": resultat["asset"],
        "agent": resultat["agent"],
        "score_technique": score,
        "taux_couverture": couverture,
        "total_controles": total,
        "controles_evalues": nombre_evalues,
        "controles_reussis": reussis,
        "controles_en_echec": controles_en_echec,
        "controles_en_attention": controles_en_attention,
        "controles_non_verifies": controles_non_verifies,
        "controles_ignores": compteur_statuts["ignore"],
        "controles_non_applicables": compteur_statuts["non_applicable"],
        "controles_problematiques": (
            controles_en_echec + controles_en_attention
        ),
        "statuts": dict(compteur_statuts),
        "severites": dict(compteur_severites),
        "actions_correctives": [
            {
                "control_id": check["control_id"],
                "severity": check["severity"],
                "status": check["status"],
                "message": check["message"],
            }
            for check in trier_actions(actions_correctives)
        ],
        "actions_verification": [
            {
                "control_id": check["control_id"],
                "severity": check["severity"],
                "status": check["status"],
                "message": check["message"],
            }
            for check in trier_actions(actions_verification)
        ],
    }
