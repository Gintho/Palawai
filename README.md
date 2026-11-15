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
app.py, vercel.json                     # bot Telegram + cron quotidien sur Vercel
.github/workflows/daily-surf-forecast.yml   # envoi manuel (secours)
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

## Fonctionnement (Vercel)

Le bot tourne sur Vercel (projet `palawai-surf`, https://palawai-surf.vercel.app) :

- **À la demande** : envoie `surf` (ou `/surf`) au bot Telegram → forecast du jour et de demain.
- **Chaque matin** : Vercel Cron appelle `/api/cron` vers 6h-7h (heure de Paris en hiver).
- Code : `app.py` → `surf_forecast/web.py` (webhook `/api/telegram`, cron `/api/cron`,
  branchement `/api/setup?key=<WEBHOOK_SECRET>`).

Variables d'environnement Vercel : `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`,
`WEBHOOK_SECRET`, `CRON_SECRET`. Après un changement de token, rouvrir
`https://palawai-surf.vercel.app/api/setup?key=<WEBHOOK_SECRET>` pour rebrancher le webhook.

Le workflow GitHub Actions reste disponible en lancement manuel (secrets
`TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`).

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
