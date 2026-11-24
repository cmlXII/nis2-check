import os
import shutil
from pathlib import Path

from nis2check.execution import lancer


def _analyser_ssh(texte):
    reglages = {"permitrootlogin": "prohibit-password", "passwordauthentication": "yes"}
    vus = set()
    for ligne in texte.splitlines():
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


def controle_ssh(chemin="/etc/ssh/sshd_config", hote=None):
    if hote:
        texte = lancer(["cat", chemin], hote)
        if not texte:
            return ("ssh", "ignoré", "Configuration SSH illisible sur la machine distante")
        return _analyser_ssh(texte)
    fichier = Path(chemin)
    if not fichier.exists():
        return ("ssh", "ignoré", "Aucun serveur SSH installé")
    return _analyser_ssh(fichier.read_text())


def controle_ports(hote=None):
    sortie = lancer(["ss", "-tln"], hote)
    ports = []
    for ligne in sortie.splitlines()[1:]:
        adresse = ligne.split()[3]
        if not adresse.startswith("127.") and not adresse.startswith("[::1]"):
            ports.append(adresse.rsplit(":", 1)[-1])
    if ports:
        return ("ports", "attention", "Ports en écoute : " + ", ".join(sorted(set(ports))))
    return ("ports", "ok", "Aucun port exposé sur le réseau")


def controle_pare_feu(hote=None):
    if hote:
        return ("pare-feu", "ignoré", "Non vérifié à distance (droits root requis)")
    if os.geteuid() != 0:
        return ("pare-feu", "ignoré", "Droits root requis pour lire les règles")
    if shutil.which("ufw"):
        if "status: active" in lancer(["ufw", "status"]).lower():
            return ("pare-feu", "ok", "ufw est actif")
        return ("pare-feu", "échec", "ufw est installé mais inactif")
    if shutil.which("nft"):
        if "hook input" in lancer(["nft", "list", "ruleset"]):
            return ("pare-feu", "ok", "Des règles nftables filtrent le trafic entrant")
        return ("pare-feu", "échec", "Aucune règle nftables sur le trafic entrant")
    return ("pare-feu", "échec", "Aucun pare-feu détecté")


def controle_mises_a_jour(hote=None):
    sortie = lancer(["apt", "list", "--upgradable"], hote)
    lignes = [l for l in sortie.splitlines() if "upgradable" in l]
    if not lignes:
        return ("mises à jour", "ok", "Aucune mise à jour en attente")
    securite = [l for l in lignes if "security" in l]
    message = f"{len(lignes)} paquets à mettre à jour"
    if securite:
        return ("mises à jour", "échec", f"{message}, dont {len(securite)} de sécurité")
    return ("mises à jour", "attention", message)
