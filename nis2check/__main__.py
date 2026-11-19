from nis2check.moteur import charger_questions, poser_questions, calculer_score, actions_prioritaires
from nis2check.controles import controle_ssh, controle_ports

questions = charger_questions("data/questions.yaml")
reponses = poser_questions(questions)
score = calculer_score(questions, reponses)
print(f"\nScore de maturité NIS 2 : {score} / 100")

print("\nActions prioritaires :")
for q in actions_prioritaires(questions, reponses)[:5]:
    print(f"- [{q['theme']}] {q['question']}")

print("\nContrôles techniques :")
for nom, statut, message in (controle_ssh(), controle_ports()):
    print(f"- {nom} : {statut} - {message}")
