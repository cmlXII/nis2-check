from datetime import date
from html import escape

STYLE = """
body { font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; color: #222; }
h1 { border-bottom: 3px solid #1a4d8f; padding-bottom: .5rem; }
.score { font-size: 3rem; font-weight: bold; }
.ok { color: #1a7f37; }
.attention { color: #b36b00; }
.echec { color: #c62828; }
li { margin-bottom: .5rem; }
"""


def classe_score(score):
    if score >= 70:
        return "ok"
    if score >= 40:
        return "attention"
    return "echec"


def generer_rapport(score, actions, controles, chemin="rapport.html"):
    lignes = [
        "<!DOCTYPE html><html lang='fr'><head><meta charset='utf-8'>",
        "<title>Rapport NIS 2</title><style>" + STYLE + "</style></head><body>",
        "<h1>Rapport de diagnostic NIS 2</h1>",
        f"<p>Généré le {date.today():%d/%m/%Y}</p>",
        f"<p class='score {classe_score(score)}'>{score} / 100</p>",
        "<h2>Actions prioritaires</h2><ul>",
    ]
    for q in actions[:5]:
        lignes.append(f"<li><strong>{escape(q['theme'])}</strong> : {escape(q['question'])}</li>")
    lignes.append("</ul><h2>Contrôles techniques</h2><ul>")
    for nom, statut, message in controles:
        classe = {"ok": "ok", "échec": "echec"}.get(statut, "attention")
        lignes.append(f"<li class='{classe}'>{escape(nom)} : {escape(statut)} - {escape(message)}</li>")
    lignes.append("</ul></body></html>")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("\n".join(lignes))
    return chemin
