import yaml

VALEURS = {"o": 1.0, "p": 0.5, "n": 0.0}


def charger_questions(chemin):
    with open(chemin, encoding="utf-8") as f:
        return yaml.safe_load(f)


def poser_questions(questions):
    reponses = {}
    for q in questions:
        print(f"\n[{q['theme']}] {q['question']}")
        choix = ""
        while choix not in VALEURS:
            choix = input("Oui (o) / Partiellement (p) / Non (n) : ").strip().lower()
        reponses[q["id"]] = VALEURS[choix]
    return reponses


def calculer_score(questions, reponses):
    total = sum(q["poids"] for q in questions)
    obtenu = sum(q["poids"] * reponses[q["id"]] for q in questions)
    return round(obtenu / total * 100)
