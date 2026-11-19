import subprocess
from pathlib import Path


def controle_ssh(chemin="/etc/ssh/sshd_config"):
    fichier = Path(chemin)
    if not fichier.exists():
        return ("ssh", "ignoré", "Aucun serveur SSH installé")
    problemes = []
    for ligne in fichier.read_text().splitlines():
        ligne = ligne.strip().lower()
        if ligne == "permitrootlogin yes":
            problemes.append("connexion root autorisée")
        if ligne == "passwordauthentication yes":
            problemes.append("connexion par mot de passe autorisée")
    if problemes:
        return ("ssh", "échec", ", ".join(problemes))
    return ("ssh", "ok", "Aucun réglage dangereux trouvé")


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
