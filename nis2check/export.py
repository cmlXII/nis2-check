import json
from datetime import date


def exporter_json(score, actions, controles, chemin="rapport.json"):
    donnees = {
        "date": date.today().isoformat(),
        "score": score,
        "actions_prioritaires": [
            {"id": q["id"], "theme": q["theme"], "question": q["question"], "poids": q["poids"]}
            for q in actions
        ],
        "controles": [
            {"nom": nom, "statut": statut, "message": message}
            for nom, statut, message in controles
        ],
    }
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=2)
    return chemin
