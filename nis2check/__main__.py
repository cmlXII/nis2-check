import argparse

from nis2check.moteur import charger_questions, poser_questions, calculer_score, actions_prioritaires
from nis2check.controles import controle_ssh, controle_ports, controle_pare_feu, controle_mises_a_jour
from nis2check.rapport import generer_rapport
from nis2check.export import exporter_json

parser = argparse.ArgumentParser(description="Diagnostic de préparation à NIS 2")
parser.add_argument("--hote", help="machine distante à contrôler en SSH (alias ou utilisateur@adresse)")
args = parser.parse_args()
hote = args.hote

questions = charger_questions("data/questions.yaml")
reponses = poser_questions(questions)
score = calculer_score(questions, reponses)
actions = actions_prioritaires(questions, reponses)
controles = [
    controle_ssh(hote=hote),
    controle_ports(hote=hote),
    controle_pare_feu(hote=hote),
    controle_mises_a_jour(hote=hote),
]

print(f"\nScore de maturité NIS 2 : {score} / 100")

print("\nActions prioritaires :")
for q in actions[:5]:
    print(f"- [{q['theme']}] {q['question']}")

print(f"\nContrôles techniques sur {hote or 'la machine locale'} :")
for nom, statut, message in controles:
    print(f"- {nom} : {statut} - {message}")

chemin = generer_rapport(score, actions, controles)
print(f"\nRapport généré : {chemin}")

chemin_json = exporter_json(score, actions, controles)
print(f"Export JSON : {chemin_json}")
