
import ipaddress
import os
import re
import shutil

from nis2check.execution import executer, lancer


def controle_ssh(chemin="/etc/ssh/sshd_config", hote=None):
    if not hote and not shutil.which("sshd"):
        return ("ssh", "ignoré", "Serveur OpenSSH non installé")

    resultat = executer(["sshd", "-T", "-f", chemin], hote)

    if resultat.returncode != 0:
        erreur = resultat.stderr.strip() or "Erreur inconnue"
        return (
            "ssh",
            "non vérifié",
            f"Impossible de lire la configuration SSH : {erreur}"
        )

    reglages = {}

    for ligne in resultat.stdout.splitlines():
        elements = ligne.strip().lower().split()
        if len(elements) == 2:
            reglages[elements[0]] = elements[1]

    parametres = [
        "permitrootlogin",
        "passwordauthentication",
        "pubkeyauthentication"
    ]

    manquants = [
        p for p in parametres if p not in reglages
    ]

    if manquants:
        return (
            "ssh",
            "non vérifié",
            "Paramètres absents : " + ", ".join(manquants)
        )

    root = reglages["permitrootlogin"]
    mot_de_passe = reglages["passwordauthentication"]
    cle = reglages["pubkeyauthentication"]

    problemes = []
    avertissements = []

    if mot_de_passe == "yes":
        problemes.append("connexion par mot de passe autorisée")
    elif mot_de_passe != "no":
        return (
            "ssh",
            "non vérifié",
            f"Valeur PasswordAuthentication inconnue : {mot_de_passe}"
        )

    if root == "yes":
        problemes.append("connexion root autorisée")
    elif root in (
        "prohibit-password",
        "without-password",
        "forced-commands-only"
    ):
        avertissements.append(
            "connexion root encore possible sous certaines conditions"
        )
    elif root != "no":
        return (
            "ssh",
            "non vérifié",
            f"Valeur PermitRootLogin inconnue : {root}"
        )

    if cle == "no":
        avertissements.append(
            "authentification par clé SSH désactivée"
        )
    elif cle != "yes":
        return (
            "ssh",
            "non vérifié",
            f"Valeur PubkeyAuthentication inconnue : {cle}"
        )

    if problemes:
        return ("ssh", "échec", ", ".join(problemes + avertissements))

    if avertissements:
        return ("ssh", "attention", ", ".join(avertissements))

    return (
        "ssh",
        "ok",
        "Mot de passe désactivé, connexion root interdite et clés SSH autorisées"
    )


def controle_ports(hote=None):
    resultat = executer(["ss", "-H", "-ltn"], hote)

    if resultat.returncode != 0:
        erreur = resultat.stderr.strip() or "Erreur inconnue"
        return (
            "ports",
            "non vérifié",
            f"Impossible de lire les ports en écoute : {erreur}"
        )

    ports_reseau = set()
    ports_locaux = set()

    for ligne in resultat.stdout.splitlines():
        elements = ligne.split()

        if len(elements) < 4:
            return (
                "ports",
                "non vérifié",
                "Format de sortie de la commande ss inattendu"
            )

        adresse = elements[3]

        if ":" not in adresse:
            return (
                "ports",
                "non vérifié",
                f"Adresse réseau impossible à interpréter : {adresse}"
            )

        hote_local, port = adresse.rsplit(":", 1)

        if not port.isdigit():
            return (
                "ports",
                "non vérifié",
                f"Port impossible à interpréter : {adresse}"
            )

        hote_local = hote_local.strip("[]")

        if hote_local == "*":
            ports_reseau.add(f"{port} ({adresse})")
            continue

        try:
            ip = ipaddress.ip_address(hote_local)
        except ValueError:
            return (
                "ports",
                "non vérifié",
                f"Adresse IP impossible à interpréter : {adresse}"
            )

        if ip.is_loopback:
            ports_locaux.add(f"{port} ({adresse})")
        else:
            ports_reseau.add(f"{port} ({adresse})")

    if ports_reseau:
        return (
            "ports",
            "attention",
            "Ports en écoute sur des interfaces réseau : "
            + ", ".join(sorted(ports_reseau))
            + ". Leur accessibilité réelle n'est pas vérifiée."
        )

    if ports_locaux:
        return (
            "ports",
            "ok",
            "Ports en écoute uniquement en local : "
            + ", ".join(sorted(ports_locaux))
        )

    return ("ports", "ok", "Aucun service TCP en écoute")


def _analyser_iptables(sortie):
    """Analyse les politiques et règles de la chaîne INPUT."""

    lignes = sortie.splitlines()

    politique_filtrante = any(
        re.match(r"^-P INPUT (DROP|REJECT)$", ligne.strip())
        for ligne in lignes
    )

    regles_input = [
        ligne.strip()
        for ligne in lignes
        if re.match(r"^-A INPUT\b", ligne.strip())
    ]

    regle_filtrante = any(
        re.search(r"\s-j\s+(DROP|REJECT)(?:\s|$)", ligne)
        for ligne in regles_input
    )

    return (
        bool(regles_input) or politique_filtrante,
        politique_filtrante or regle_filtrante
    )


def _analyser_nftables(sortie):
    """Recherche une chaîne nftables qui filtre le trafic entrant."""

    for index, ligne in enumerate(sortie.splitlines()):
        if not re.search(r"\bchain\s+\S+\s*\{", ligne):
            continue

        bloc = [ligne]
        profondeur = ligne.count("{") - ligne.count("}")
        position = index + 1
        lignes = sortie.splitlines()

        while profondeur > 0 and position < len(lignes):
            suivante = lignes[position]
            bloc.append(suivante)
            profondeur += suivante.count("{") - suivante.count("}")
            position += 1

        contenu = "\n".join(bloc)

        if not re.search(r"\bhook\s+input\b", contenu):
            continue

        politique_filtrante = bool(
            re.search(r"\bpolicy\s+(drop|reject)\b", contenu)
        )

        regle_filtrante = any(
            re.search(r"\b(drop|reject)\s*$", element.strip())
            for element in bloc
        )

        return (
            True,
            politique_filtrante or regle_filtrante
        )

    return False, False


def _analyser_ufw(sortie):
    """Analyse l'état UFW et sa politique entrante."""

    actif = bool(re.search(r"^Status:\s+active$", sortie, re.I | re.M))

    if not actif:
        return False, False

    politique_filtrante = bool(
        re.search(
            r"Default:\s*(deny|reject)\s*\(incoming\)",
            sortie,
            re.I
        )
    )

    regle_filtrante = bool(
        re.search(r"\b(DENY|REJECT)\s+IN\b", sortie, re.I)
    )

    return True, politique_filtrante or regle_filtrante


def controle_pare_feu(hote=None):
    if hote:
        return (
            "pare-feu",
            "non vérifié",
            "Contrôle distant non pris en charge"
        )

    if os.geteuid() != 0:
        return (
            "pare-feu",
            "non vérifié",
            "Droits root requis pour lire les règles"
        )

    backends = []
    erreurs = []
    observations = []

    filtrage_detecte = False
    regles_detectees = False

    commandes = {
        "ufw": ["ufw", "status", "verbose"],
        "nft": ["nft", "list", "ruleset"],
        "iptables": ["iptables", "-S"],
        "ip6tables": ["ip6tables", "-S"]
    }

    for nom, commande in commandes.items():
        if not shutil.which(nom):
            continue

        backends.append(nom)
        resultat = executer(commande)

        if resultat.returncode != 0:
            erreur = resultat.stderr.strip() or "Erreur inconnue"
            erreurs.append(f"{nom} : {erreur}")
            continue

        sortie = resultat.stdout.strip()

        if nom == "ufw":
            regles, filtre = _analyser_ufw(sortie)

        elif nom == "nft":
            regles, filtre = _analyser_nftables(sortie)

        else:
            regles, filtre = _analyser_iptables(sortie)

        if regles:
            regles_detectees = True
            observations.append(nom)

        if filtre:
            filtrage_detecte = True

    if not backends:
        return (
            "pare-feu",
            "non vérifié",
            "Aucun outil de vérification du pare-feu disponible"
        )

    if filtrage_detecte:
        message = (
            "Des mécanismes de filtrage entrant ont été détectés : "
            + ", ".join(observations)
            + ". Leur efficacité et leurs règles doivent être auditées."
        )

        if erreurs:
            message += " Vérifications incomplètes : " + "; ".join(erreurs)

        return ("pare-feu", "attention", message)

    if erreurs:
        return (
            "pare-feu",
            "non vérifié",
            "Impossible de vérifier tous les mécanismes : "
            + "; ".join(erreurs)
        )

    if regles_detectees:
        return (
            "pare-feu",
            "attention",
            "Des règles existent, mais un filtrage entrant effectif "
            "n'a pas pu être confirmé : " + ", ".join(observations)
        )

    return (
        "pare-feu",
        "échec",
        "Aucune politique de filtrage entrant détectée "
        "dans les mécanismes vérifiés"
    )


def controle_mises_a_jour(hote=None):
    resultat = executer(["apt", "list", "--upgradable"], hote)

    if resultat.returncode != 0:
        erreur = resultat.stderr.strip() or "Erreur inconnue"
        return (
            "mises à jour",
            "non vérifié",
            f"Impossible de vérifier les mises à jour : {erreur}"
        )

    sortie = resultat.stdout.strip()

    if not sortie:
        return (
            "mises à jour",
            "non vérifié",
            "La commande APT n'a retourné aucun résultat"
        )

    lignes = sortie.splitlines()

    if lignes[0].strip() != "Listing...":
        return (
            "mises à jour",
            "non vérifié",
            "Format de sortie APT inattendu"
        )

    paquets = []

    for ligne in lignes[1:]:
        ligne = ligne.strip()

        if not ligne:
            continue

        if not re.search(r"\[upgradable from: .+\]$", ligne):
            return (
                "mises à jour",
                "non vérifié",
                f"Ligne APT impossible à interpréter : {ligne}"
            )

        paquets.append(ligne)

    if not paquets:
        return (
            "mises à jour",
            "ok",
            "Aucune mise à jour en attente"
        )

    return (
        "mises à jour",
        "attention",
        f"{len(paquets)} paquets à mettre à jour. "
        "La nature sécuritaire des mises à jour n'est pas déterminée."
    )

