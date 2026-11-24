from nis2check.export import exporter_json
from nis2check.moteur import charger_questions, poser_questions, calculer_score, actions_prioritaires
from nis2check.controles import controle_ssh, controle_ports, controle_pare_feu, controle_mises_a_jour
from nis2check.rapport import generer_rapport

questions = charger_questions("data/questions.yaml")
reponses = poser_questions(questions)
score = calculer_score(questions, reponses)
actions = actions_prioritaires(questions, reponses)
controles = [controle_ssh(), controle_ports(), controle_pare_feu(), controle_mises_a_jour()]

print(f"\nScore de maturité NIS 2 : {score} / 100")

print("\nActions prioritaires :")
for q in actions[:5]:
    print(f"- [{q['theme']}] {q['question']}")

print("\nContrôles techniques :")
for nom, statut, message in controles:
    print(f"- {nom} : {statut} - {message}")

chemin = generer_rapport(score, actions, controles)
print(f"\nRapport généré : {chemin}")

chemin_json = exporter_json(score, actions, controles)
print(f"Export JSON : {chemin_json}")
