
from datetime import date
from html import escape


STYLE = """
* { box-sizing: border-box; }

body {
    font-family: Arial, sans-serif;
    max-width: 1000px;
    margin: 2rem auto;
    padding: 0 1.5rem;
    color: #263238;
    background: #f4f6f9;
    line-height: 1.6;
}

header, section, footer {
    background: white;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    border-radius: 10px;
}

header {
    border-top: 5px solid #1a4d8f;
}

h1, h2 {
    color: #17365d;
}

h1 {
    margin-top: 0;
}

h2 {
    border-bottom: 1px solid #e1e5eb;
    padding-bottom: .5rem;
}

.date, .muted {
    color: #65717d;
    font-size: .9rem;
}

.score {
    font-size: 3rem;
    font-weight: bold;
    color: #1a4d8f;
    margin: .5rem 0;
}

.score-label {
    font-size: .9rem;
    color: #65717d;
}

.stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 1rem;
    margin-top: 1rem;
}

.stat {
    background: #f4f6f9;
    padding: 1rem;
    border-radius: 8px;
}

.stat strong {
    display: block;
    font-size: 1.5rem;
}

.ok { color: #18753b; }
.attention { color: #a76500; }
.echec { color: #bd2929; }
.neutre { color: #596675; }

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
}

th, td {
    padding: .8rem;
    border-bottom: 1px solid #e1e5eb;
    text-align: left;
    vertical-align: top;
}

th {
    background: #f4f6f9;
    color: #17365d;
}

ul, ol {
    padding-left: 1.5rem;
}

li {
    margin-bottom: .8rem;
}

.action-theme {
    color: #65717d;
    font-size: .85rem;
}

footer {
    color: #65717d;
    font-size: .85rem;
}

@media (max-width: 600px) {
    body { padding: 0 .5rem; }
    header, section, footer { padding: 1rem; }
    table { font-size: .85rem; }
}
"""


def classe_score(score):
    if score >= 70:
        return "ok"
    if score >= 40:
        return "attention"
    return "echec"


def classe_statut(statut):
    classes = {
        "ok": "ok",
        "attention": "attention",
        "échec": "echec",
        "non vérifié": "neutre",
        "ignoré": "neutre"
    }
    return classes.get(statut, "neutre")


def generer_rapport(score, actions, controles, chemin="rapport.html"):
    statuts = [
        "ok",
        "attention",
        "échec",
        "non vérifié",
        "ignoré"
    ]

    compteur = {
        statut: sum(1 for _, s, _ in controles if s == statut)
        for statut in statuts
    }

    lignes = [
        "<!DOCTYPE html>",
        "<html lang='fr'>",
        "<head>",
        "<meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<title>Rapport de diagnostic NIS2-Check</title>",
        "<style>",
        STYLE,
        "</style>",
        "</head>",
        "<body>",

        "<header>",
        "<h1>NIS2-Check</h1>",
        "<p>Rapport de diagnostic de cybersécurité</p>",
        f"<p class='date'>Date du diagnostic : {date.today():%d/%m/%Y}</p>",
        "<div class='score'>",
        f"{score} / 100",
        "</div>",
        "<p class='score-label'>Score indicatif de maturité organisationnelle, "
        "calculé à partir des réponses au questionnaire.</p>",
        "</header>",

        "<section>",
        "<h2>1. Résumé exécutif</h2>",
        "<p>Ce rapport présente les résultats d'un questionnaire "
        "de maturité organisationnelle et de contrôles techniques "
        "effectués sur le système audité.</p>",
        "<p>Le score présenté mesure les réponses déclaratives. "
        "Il ne constitue pas une mesure de conformité réglementaire "
        "ni une certification NIS2.</p>",
        "<div class='stats'>",
    ]

    for statut in statuts:
        lignes.append(
            f"<div class='stat {classe_statut(statut)}'>"
            f"<strong>{compteur[statut]}</strong>"
            f"{escape(statut.capitalize())}"
            "</div>"
        )

    lignes.extend([
        "</div>",
        "</section>",

        "<section>",
        "<h2>2. Actions prioritaires</h2>",
    ])

    if actions:
        lignes.append("<ol>")

        for question in actions:
            theme = escape(str(question.get("theme", "Sans thème")))
            texte = escape(str(question.get("question", "")))

            lignes.append(
                "<li>"
                f"<span class='action-theme'>{theme}</span><br>"
                f"{texte}"
                "</li>"
            )

        lignes.append("</ol>")
    else:
        lignes.append(
            "<p>Aucune action prioritaire identifiée "
            "à partir des réponses fournies.</p>"
        )

    lignes.extend([
        "</section>",

        "<section>",
        "<h2>3. Résultats des contrôles techniques</h2>",
    ])

    if controles:
        lignes.extend([
            "<table>",
            "<thead>",
            "<tr>",
            "<th>Contrôle</th>",
            "<th>Statut</th>",
            "<th>Résultat</th>",
            "</tr>",
            "</thead>",
            "<tbody>"
        ])

        for nom, statut, message in controles:
            classe = classe_statut(statut)

            lignes.append(
                "<tr>"
                f"<td>{escape(str(nom))}</td>"
                f"<td class='{classe}'><strong>{escape(str(statut))}</strong></td>"
                f"<td>{escape(str(message))}</td>"
                "</tr>"
            )

        lignes.extend([
            "</tbody>",
            "</table>"
        ])
    else:
        lignes.append("<p>Aucun contrôle technique effectué.</p>")

    lignes.extend([
        "</section>",

        "<section>",
        "<h2>4. Méthodologie et limites</h2>",
        "<ul>",
        "<li>Le score organisationnel repose sur les réponses "
        "fournies au questionnaire.</li>",
        "<li>Les contrôles techniques sont indépendants du score "
        "organisationnel.</li>",
        "<li>Un contrôle non vérifié ou ignoré ne signifie pas "
        "que le système est sécurisé.</li>",
        "<li>Les résultats dépendent des informations accessibles "
        "et des permissions disponibles au moment du diagnostic.</li>",
        "<li>Ce rapport ne remplace pas un audit de cybersécurité "
        "complet ni une analyse juridique de l'assujettissement à NIS2.</li>",
        "</ul>",
        "</section>",

        "<footer>",
        "<strong>NIS2-Check</strong>",
        "<p>Outil d'aide au diagnostic et à l'amélioration "
        "de la posture de cybersécurité.</p>",
        "</footer>",

        "</body>",
        "</html>"
    ])

    with open(chemin, "w", encoding="utf-8") as fichier:
        fichier.write("\n".join(lignes))

    return chemin
