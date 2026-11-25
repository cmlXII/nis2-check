
import shlex
import subprocess


def _texte(valeur):
    """Convertit une sortie de commande en texte."""
    if valeur is None:
        return ""

    if isinstance(valeur, bytes):
        return valeur.decode("utf-8", errors="replace")

    return valeur


def executer(commande, hote=None, timeout=15):
    """
    Exécute une commande localement ou à distance en SSH.

    Retourne toujours un objet contenant :
    - stdout : sortie normale
    - stderr : sortie d'erreur
    - returncode : code de retour
    """

    commande = ["env", "LC_ALL=C"] + commande

    if hote:
        commande = [
            "ssh",
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=10",
            "-o", "ServerAliveInterval=5",
            "-o", "ServerAliveCountMax=2",
            "--",
            hote,
            shlex.join(commande)
        ]

    try:
        return subprocess.run(
            commande,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )

    except subprocess.TimeoutExpired as erreur:
        return subprocess.CompletedProcess(
            args=commande,
            returncode=124,
            stdout=_texte(erreur.stdout),
            stderr=f"Commande interrompue : délai de {timeout} secondes dépassé."
        )

    except FileNotFoundError:
        return subprocess.CompletedProcess(
            args=commande,
            returncode=127,
            stdout="",
            stderr=f"Commande introuvable : {commande[0]}"
        )

    except OSError as erreur:
        return subprocess.CompletedProcess(
            args=commande,
            returncode=1,
            stdout="",
            stderr=f"Erreur système : {erreur}"
        )


def lancer(commande, hote=None, timeout=15):
    """Conserve la compatibilité avec les anciens contrôles."""
    resultat = executer(commande, hote, timeout)
    return resultat.stdout

