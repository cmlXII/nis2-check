import subprocess
from pathlib import Path


def controle_ssh(chemin="/etc/ssh/sshd_config"):
    fichier = Path(chemin)
    if not fichier.exists():
        return ("ssh", "ignoré", "Aucun serveur SSH installé")
    reglages = {"permitrootlogin": "prohibit-password", "passwordauthentication": "yes"}
    vus = set()
    for ligne in fichier.read_text().splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#"):
            continue
        mots = ligne.split()
        cle = mots[0].lower()
        if len(mots) >= 2 and cle in reglages and cle not in vus:
            reglages[cle] = mots[1].lower()
            vus.add(cle)
    problemes = []
    if reglages["permitrootlogin"] == "yes":
        problemes.append("connexion root par mot de passe autorisée")
    if reglages["passwordauthentication"] == "yes":
        problemes.append("connexion par mot de passe autorisée")
    if problemes:
        return ("ssh", "échec", ", ".join(problemes))
    return ("ssh", "ok", "Connexion par clé uniquement, root bloqué")


def controle_ports():
    sortie = subprocess.run(["ss", "-tln"], capture_output=True, text=True).stdout
    ports = []
    for ligne in sortie.splitlines()[1:]:
        adresse = ligne.split()[3]
        if not adresse.startswith("127.") and not adresse.startswith("[::1]"):
            ports.append(adresse.rsplit(":", 1)[-1])
    if ports:
        return ("ports", "attention", "Ports en écoute : " + ", ".join(sorted(set(ports))))
    return ("ports", "ok", "Aucun port exposé sur le réseau")
