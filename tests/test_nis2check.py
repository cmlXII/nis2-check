
import json
from types import SimpleNamespace

from nis2check import execution, controles
from nis2check.moteur import calculer_score, actions_prioritaires
from nis2check.controles import controle_ssh
from nis2check.export import exporter_json


QUESTIONS = [
    {"id": "a", "theme": "T1", "question": "Question A", "poids": 3},
    {"id": "b", "theme": "T2", "question": "Question B", "poids": 1},
]


def resultat_commande(stdout="", stderr="", returncode=0):
    return SimpleNamespace(
        stdout=stdout,
        stderr=stderr,
        returncode=returncode
    )


def simuler_commande(monkeypatch, resultat):
    monkeypatch.setattr(controles, "executer", lambda *a, **k: resultat)
    monkeypatch.setattr(controles, "lancer", lambda *a, **k: resultat.stdout)


# Tests du moteur

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


# Tests SSH

def test_ssh_detecte_mot_de_passe_autorise(monkeypatch):
    sortie = """
permitrootlogin no
passwordauthentication yes
pubkeyauthentication yes
"""
    simuler_commande(monkeypatch, resultat_commande(stdout=sortie))
    assert controle_ssh()[1] == "échec"


def test_ssh_detecte_root_autorise(monkeypatch):
    sortie = """
permitrootlogin yes
passwordauthentication no
pubkeyauthentication yes
"""
    simuler_commande(monkeypatch, resultat_commande(stdout=sortie))
    assert controle_ssh()[1] == "échec"


def test_ssh_configuration_securisee(monkeypatch):
    sortie = """
permitrootlogin no
passwordauthentication no
pubkeyauthentication yes
"""
    simuler_commande(monkeypatch, resultat_commande(stdout=sortie))
    assert controle_ssh()[1] == "ok"


def test_ssh_configuration_root_limitee(monkeypatch):
    sortie = """
permitrootlogin prohibit-password
passwordauthentication no
pubkeyauthentication yes
"""
    simuler_commande(monkeypatch, resultat_commande(stdout=sortie))
    assert controle_ssh()[1] == "attention"


def test_ssh_commande_en_erreur(monkeypatch):
    resultat = resultat_commande(stderr="Permission denied", returncode=1)
    simuler_commande(monkeypatch, resultat)
    assert controle_ssh()[1] == "non vérifié"


# Tests des mises à jour

def test_mises_a_jour_aucune(monkeypatch):
    simuler_commande(monkeypatch, resultat_commande(stdout="Listing...\n"))
    assert controles.controle_mises_a_jour()[1] == "ok"


def test_mises_a_jour_disponibles(monkeypatch):
    sortie = (
        "Listing...\n"
        "apache2-bin/kali-rolling 2.4.69-1 amd64 "
        "[upgradable from: 2.4.68-2]\n"
    )
    simuler_commande(monkeypatch, resultat_commande(stdout=sortie))
    assert controles.controle_mises_a_jour()[1] == "attention"


def test_mises_a_jour_commande_en_erreur(monkeypatch):
    resultat = resultat_commande(
        stderr="Temporary failure resolving repository",
        returncode=100
    )
    simuler_commande(monkeypatch, resultat)
    assert controles.controle_mises_a_jour()[1] == "non vérifié"


def test_mises_a_jour_sortie_invalide(monkeypatch):
    simuler_commande(monkeypatch, resultat_commande(stdout=""))
    assert controles.controle_mises_a_jour()[1] == "non vérifié"


# Test de l'export JSON

def test_export_json(tmp_path):
    chemin = tmp_path / "rapport.json"
    actions = [{"id": "a", "theme": "T", "question": "Q", "poids": 3}]

    exporter_json(80, actions, [("ssh", "ok", "bien")], str(chemin))

    donnees = json.loads(chemin.read_text(encoding="utf-8"))

    assert donnees["score"] == 80
    assert donnees["actions_prioritaires"][0]["id"] == "a"
    assert donnees["controles"][0]["statut"] == "ok"


# Tests de l'exécution

def test_execution_timeout(monkeypatch):
    def simuler_timeout(*args, **kwargs):
        raise execution.subprocess.TimeoutExpired(
            cmd=args[0], timeout=15, output=b"sortie partielle"
        )

    monkeypatch.setattr(execution.subprocess, "run", simuler_timeout)
    resultat = execution.executer(["sleep", "30"])

    assert resultat.returncode == 124
    assert "dépassé" in resultat.stderr
    assert resultat.stdout == "sortie partielle"


def test_execution_commande_introuvable(monkeypatch):
    monkeypatch.setattr(
        execution.subprocess, "run",
        lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError())
    )
    resultat = execution.executer(["commande"])

    assert resultat.returncode == 127
    assert "Commande introuvable" in resultat.stderr


def test_execution_erreur_systeme(monkeypatch):
    monkeypatch.setattr(
        execution.subprocess, "run",
        lambda *a, **k: (_ for _ in ()).throw(OSError("Erreur de test"))
    )
    resultat = execution.executer(["commande"])

    assert resultat.returncode == 1
    assert "Erreur système" in resultat.stderr


# Tests du pare-feu

def simuler_pare_feu(monkeypatch, resultats):
    monkeypatch.setattr(controles.os, "geteuid", lambda: 0)
    monkeypatch.setattr(
        controles.shutil,
        "which",
        lambda nom: nom if nom in resultats else None
    )

    def executer_simulee(commande, *args, **kwargs):
        return resultats[commande[0]]

    monkeypatch.setattr(controles, "executer", executer_simulee)


def test_pare_feu_aucun_filtrage(monkeypatch):
    resultats = {
        "iptables": resultat_commande(
            stdout="-P INPUT ACCEPT\n-P FORWARD ACCEPT\n-P OUTPUT ACCEPT\n"
        ),
        "ip6tables": resultat_commande(
            stdout="-P INPUT ACCEPT\n-P FORWARD ACCEPT\n-P OUTPUT ACCEPT\n"
        ),
        "nft": resultat_commande(stdout="")
    }
    simuler_pare_feu(monkeypatch, resultats)
    assert controles.controle_pare_feu()[1] == "échec"


def test_pare_feu_iptables_filtrage_detecte(monkeypatch):
    resultats = {
        "iptables": resultat_commande(stdout="-P INPUT DROP\n"),
        "ip6tables": resultat_commande(stdout="-P INPUT ACCEPT\n")
    }
    simuler_pare_feu(monkeypatch, resultats)
    assert controles.controle_pare_feu()[1] == "attention"


def test_pare_feu_regle_drop_detectee(monkeypatch):
    resultats = {
        "iptables": resultat_commande(
            stdout="-P INPUT ACCEPT\n-A INPUT -p tcp -j DROP\n"
        )
    }
    simuler_pare_feu(monkeypatch, resultats)
    assert controles.controle_pare_feu()[1] == "attention"


def test_pare_feu_ipv6_filtrage_detecte(monkeypatch):
    resultats = {
        "ip6tables": resultat_commande(stdout="-P INPUT REJECT\n")
    }
    simuler_pare_feu(monkeypatch, resultats)
    assert controles.controle_pare_feu()[1] == "attention"


def test_pare_feu_nftables_filtrage_detecte(monkeypatch):
    sortie = """
table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;
    }
}
"""
    resultats = {"nft": resultat_commande(stdout=sortie)}
    simuler_pare_feu(monkeypatch, resultats)
    assert controles.controle_pare_feu()[1] == "attention"


def test_pare_feu_ufw_actif(monkeypatch):
    sortie = """
Status: active
Logging: on
Default: deny (incoming), allow (outgoing), disabled (routed)
"""
    resultats = {"ufw": resultat_commande(stdout=sortie)}
    simuler_pare_feu(monkeypatch, resultats)
    assert controles.controle_pare_feu()[1] == "attention"


def test_pare_feu_sans_droits_root(monkeypatch):
    monkeypatch.setattr(controles.os, "geteuid", lambda: 1000)

    resultat = controles.controle_pare_feu()

    assert resultat[1] == "non vérifié"
    assert "Droits root requis" in resultat[2]


def test_pare_feu_erreur_verification(monkeypatch):
    resultats = {
        "iptables": resultat_commande(
            stderr="Permission denied", returncode=1
        )
    }
    simuler_pare_feu(monkeypatch, resultats)
    assert controles.controle_pare_feu()[1] == "non vérifié"

