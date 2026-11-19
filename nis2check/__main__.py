from nis2check.moteur import charger_questions, poser_questions, calculer_score

questions = charger_questions("data/questions.yaml")
reponses = poser_questions(questions)
score = calculer_score(questions, reponses)
print(f"\nScore de maturité NIS 2 : {score} / 100")
