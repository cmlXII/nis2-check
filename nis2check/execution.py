import shlex
import subprocess


def lancer(commande, hote=None):
    commande = ["env", "LC_ALL=C"] + commande
    if hote:
        commande = ["ssh", "-o", "BatchMode=yes", "--", hote, shlex.join(commande)]
    return subprocess.run(commande, capture_output=True, text=True).stdout
