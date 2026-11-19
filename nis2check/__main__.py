from nis2check.moteur import charger_questions, poser_questions, calculer_score, actions_prioritaires

questions = charger_questions("data/questions.yaml")
reponses = poser_questions(questions)
score = calculer_score(questions, reponses)
print(f"\nScore de maturité NIS 2 : {score} / 100")

print("\nActions prioritaires :")
for q in actions_prioritaires(questions, reponses)[:5]:
    print(f"- [{q['theme']}] {q['question']}")
