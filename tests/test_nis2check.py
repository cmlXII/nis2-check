from nis2check.moteur import calculer_score, actions_prioritaires
from nis2check.controles import controle_ssh

QUESTIONS = [
    {"id": "a", "theme": "T1", "question": "Question A", "poids": 3},
    {"id": "b", "theme": "T2", "question": "Question B", "poids": 1},
]


def test_score_tout_oui():
    assert calculer_score(QUESTIONS, {"a": 1.0, "b": 1.0}) == 100


def test_score_tout_non():
    assert calculer_score(QUESTIONS, {"a": 0.0, "b": 0.0}) == 0


def test_score_partiel():
    assert calculer_score(QUESTIONS, {"a": 0.5, "b": 0.5}) == 50


def test_le_poids_compte():
    assert calculer_score(QUESTIONS, {"a": 1.0, "b": 0.0}) == 75


def test_actions_triees_par_poids():
    actions = actions_prioritaires(QUESTIONS, {"a": 0.0, "b": 0.0})
    assert actions[0]["id"] == "a"


def test_actions_ignorent_les_oui():
    actions = actions_prioritaires(QUESTIONS, {"a": 1.0, "b": 0.0})
    assert [q["id"] for q in actions] == ["b"]


def test_ssh_detecte_mot_de_passe(tmp_path):
    config = tmp_path / "sshd_config"
    config.write_text("PasswordAuthentication yes\n")
    assert controle_ssh(str(config))[1] == "échec"


def test_ssh_ok_si_mot_de_passe_desactive(tmp_path):
    config = tmp_path / "sshd_config"
    config.write_text("PasswordAuthentication no\nPermitRootLogin no\n")
    assert controle_ssh(str(config))[1] == "ok"


def test_ssh_ligne_commentee_utilise_la_valeur_par_defaut(tmp_path):
    config = tmp_path / "sshd_config"
    config.write_text("#PasswordAuthentication no\n")
    assert controle_ssh(str(config))[1] == "échec"
