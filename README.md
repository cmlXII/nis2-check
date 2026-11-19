# nis2-check

Outil en ligne de commande qui aide les PME à évaluer leur niveau de préparation à la directive européenne NIS 2.

## Fonctionnalités

- Questionnaire de maturité basé sur les mesures de l'article 21 de la directive (12 questions pondérées)
- Score de maturité sur 100 et liste des actions prioritaires
- Contrôles techniques automatiques : configuration SSH et ports ouverts
- Rapport HTML prêt à présenter

## Installation

```bash
git clone git@github.com:cmlXII/nis2-check.git
cd nis2-check
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Utilisation

```bash
python -m nis2check
```

Le programme pose les questions, lance les contrôles techniques sur la machine locale et génère `rapport.html`.

## Limites

Projet pédagogique en cours de développement : il ne remplace pas un audit et la transposition française de NIS 2 n'est pas encore définitive.
Les contrôles techniques ne doivent être lancés que sur des machines dont vous êtes responsable.
