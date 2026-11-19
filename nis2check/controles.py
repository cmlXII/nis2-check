import os
import shutil
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


def _lancer(commande):
    env = {**os.environ, "LC_ALL": "C"}
    return subprocess.run(commande, capture_output=True, text=True, env=env).stdout


def controle_pare_feu():
    if os.geteuid() != 0:
        return ("pare-feu", "ignoré", "Droits root requis pour lire les règles")
    if shutil.which("ufw"):
        if "status: active" in _lancer(["ufw", "status"]).lower():
            return ("pare-feu", "ok", "ufw est actif")
        return ("pare-feu", "échec", "ufw est installé mais inactif")
    if shutil.which("nft"):
        if "hook input" in _lancer(["nft", "list", "ruleset"]):
            return ("pare-feu", "ok", "Des règles nftables filtrent le trafic entrant")
        return ("pare-feu", "échec", "Aucune règle nftables sur le trafic entrant")
    return ("pare-feu", "échec", "Aucun pare-feu détecté")


def controle_mises_a_jour():
    sortie = _lancer(["apt", "list", "--upgradable"])
    lignes = [l for l in sortie.splitlines() if "upgradable" in l]
    if not lignes:
        return ("mises à jour", "ok", "Aucune mise à jour en attente")
    securite = [l for l in lignes if "security" in l]
    message = f"{len(lignes)} paquets à mettre à jour"
    if securite:
        return ("mises à jour", "échec", f"{message}, dont {len(securite)} de sécurité")
    return ("mises à jour", "attention", message)
