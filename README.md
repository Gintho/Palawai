# 🏄 Palawai — Agent BMAD « Kai », surf forecast Palavas / Carnon

Kai est un **agent BMAD custom (type expert, avec sidecar)** qui envoie chaque matin sur
Telegram le forecast surf de Palavas-les-Flots, Carnon et Maguelone, avec un verdict
clair : 🔥 idéal · ✅ bon · 🤏 surfable · 😐 bof · ❌ flat.

## Structure

```
_bmad/custom/agents/surf-forecaster/
├── surf-forecaster.agent.yaml          # persona, principes, menu (*forecast, *send, *spots…)
└── surf-forecaster-sidecar/
    ├── spots.yaml                      # spots + conditions idéales + grille de notation
    └── instructions.md                 # méthode de prévision de l'agent
surf_forecast/                          # moteur : Open-Meteo → score → message Telegram
.github/workflows/daily-surf-forecast.yml   # envoi quotidien automatique (≈ 6h15)
```

## Les spots

| Spot | Houle idéale | Vent idéal (offshore) | Niveau |
|---|---|---|---|
| Palavas – Plage des Coquilles | SE, 0,8–1,8 m | NNO (Tramontane/Mistral) | Débutant → inter |
| Palavas – Rive droite (La Mairie) | SSE, 0,8–1,8 m | NNO | Intermédiaire |
| Carnon – Les Roquilles | S, 0,7–1,6 m | NO | Débutant → inter |
| Carnon – Petit / Grand Travers | SE, 0,8–1,8 m | NO | Tous niveaux |
| Maguelone | SSE, 0,8–1,6 m | N-NNO | Inter → confirmé |

**La règle d'or en Méditerranée** : une houle de SE/S levée par 1 à 3 jours de Marin,
puis le vent qui tourne au NO (ou tombe). Période ≥ 6 s, sinon c'est du clapot.
La marée est négligeable.

## Mise en place de l'envoi Telegram (5 min)

1. Sur Telegram, écris à **@BotFather** → `/newbot` → récupère le **token**.
2. Envoie un message quelconque à ton nouveau bot, puis ouvre
   `https://api.telegram.org/bot<TOKEN>/getUpdates` et note `"chat":{"id": …}` → c'est ton **chat id**.
3. Sur GitHub : *Settings → Secrets and variables → Actions → New repository secret* :
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. *Actions → Daily surf forecast → Run workflow* pour tester tout de suite.
   Ensuite, ça part tout seul chaque matin (le cron GitHub ne tourne que depuis la branche par défaut).

Changer l'heure : modifie la ligne `cron` du workflow (heure UTC).

## En local

```bash
pip install -r requirements.txt
python -m surf_forecast --dry-run     # affiche le message
python -m unittest discover -s tests
```

## Utiliser l'agent dans BMAD

Installe BMAD (`npx bmad-method install`), ajoute le dossier `_bmad/custom/agents/surf-forecaster`
comme agent custom, puis active **Kai** et utilise `*forecast`, `*send`, `*spots`, `*conditions`, `*schedule`.

Sources des spots : surf-forecast.com, surfnerd.com, surf-report.com, plages.tv.
Données de prévision : [Open-Meteo](https://open-meteo.com) (gratuit, sans clé).
