# 🏄 Palawai — Kai, le bot surf de Palavas / Carnon

**Kai** est un agent **BMAD** (custom, type *expert* avec sidecar) doublé d'un **bot Telegram**.
Quand tu lui écris **`surf`** sur Telegram, il analyse la houle et le vent sur les spots de
Palavas-les-Flots, Carnon et Maguelone, et te dit clairement s'il faut aller surfer :

> 🔥 Idéal · ✅ Bon · 🤏 Surfable · 😐 Bof · ❌ Flat

- 📲 **Uniquement à la demande** : envoie `surf` au bot Telegram → forecast d'aujourd'hui et de demain.
- 🔕 **Aucun envoi automatique** : le bot ne t'écrit jamais de lui-même.
- 🆓 **100 % gratuit** : prévisions [Open-Meteo](https://open-meteo.com) (sans clé), hébergement Vercel (offre Hobby).

---

## Sommaire

1. [Exemple de message](#exemple-de-message)
2. [Les spots et les conditions idéales](#les-spots-et-les-conditions-idéales)
3. [Comment Kai note les conditions](#comment-kai-note-les-conditions)
4. [Utilisation au quotidien](#utilisation-au-quotidien)
5. [Architecture](#architecture)
6. [Installation / réinstallation](#installation--réinstallation)
7. [Personnaliser](#personnaliser)
8. [Dépannage](#dépannage)
9. [L'agent BMAD](#lagent-bmad)
10. [Développement local](#développement-local)

---

## Exemple de message

```
🏄 Surf Forecast Palavas / Carnon
📅 Samedi 14 nov.

━━━ AUJOURD'HUI — Samedi 14 nov. ━━━
✅ Carnon – Plage des Roquilles — 6.4/10
   🌊 0.6 m · 6 s (bon) · S
   💨 8 km/h (raf. 13) N · offshore
   ⏰ Créneau : 07:00 → 09:00
🤏 Palavas – Plage des Coquilles — 5.3/10
   ...

👉 Verdict : ✅ Bon — ça vaut le coup
   Meilleur spot : Carnon – Plage des Roquilles (07:00-09:00)

━━━ DEMAIN — Dimanche 15 nov. ━━━
🔥 Carnon – Petit / Grand Travers — 8.6/10
   🌊 1.4 m · 6 s (bon) · SE
   💨 8 km/h (raf. 15) E · glassy
   ⏰ Créneau : 07:00 → 14:00
   ...

🌡️ Eau : 16°C → combi 3/2 mm
```

Pour chaque spot : note /10, hauteur · période · direction de houle, vent et rafales,
meilleur créneau horaire. Kai signale aussi la **rotation Marin → Tramontane** (la
meilleure fenêtre en Méditerranée), la combinaison à prendre, et prévient quand c'est gros.

## Les spots et les conditions idéales

| Spot | Houle idéale | Vent idéal (de terre) | Niveau |
|---|---|---|---|
| Palavas – Plage des Coquilles | SE, 0,8–1,8 m | NNO (Tramontane / Mistral) | Débutant → intermédiaire |
| Palavas – Rive droite (La Mairie) | SSE, 0,8–1,8 m | NNO | Intermédiaire |
| Carnon – Les Roquilles | S, 0,7–1,6 m | NO | Débutant → intermédiaire |
| Carnon – Petit / Grand Travers | SE, 0,8–1,8 m | NO | Tous niveaux |
| Maguelone (bonus) | SSE, 0,8–1,6 m | N à NNO | Intermédiaire → confirmé |

**La règle d'or en Méditerranée** : 1 à 3 jours de **Marin** (vent de SE) lèvent une houle
de SE/S, puis le vent **tourne au NO** (Tramontane / Mistral) ou tombe → mer lisse avec
encore de la houle. Il faut une **période ≥ 6 s**, sinon c'est du clapot. La marée est
négligeable (20-30 cm).

Les sources ne sont pas toutes d'accord (Palavas est donné pour débutants ou pour
intermédiaires selon les sites) ; toutes s'accordent sur un point : ces spots ne marchent
que quelques jours par mois. Coordonnées et directions sont des estimations, ajustables
dans [`spots.yaml`](_bmad/custom/agents/surf-forecaster/surf-forecaster-sidecar/spots.yaml).

Sources : [surf-forecast.com](https://www.surf-forecast.com/breaks/Palavasles-Flots),
[surfnerd](https://surfnerd.com/surf-forecast/carnon),
[surf-report.com](https://www.surf-report.com/surf-info/palavas-flots-s1066.html),
[plages.tv](https://www.plages.tv/surf/spot/plage-des-coquilles-palavas-les-flots-34250).

## Comment Kai note les conditions

Pour chaque heure de jour (7h-19h) et chaque spot :

```
score = taille × période × direction de houle × vent      (plafonné à 10)
```

| Critère | Règle |
|---|---|
| **Taille** | < 0,3 m = 0 · sous le minimum du spot = 2 · monte jusqu'à 10 dans la plage idéale · décroît au-delà (gros = désordonné) |
| **Période** | facteur 0,35 (< 4 s, clapot) → 0,6 (< 5 s) → 0,85 (< 6 s) → 1,0 (6-8 s) → 1,1 (≥ 8 s) |
| **Direction de houle** | 1,0 au centre de la fenêtre du spot → 0,6 au bord → 0,2 hors fenêtre |
| **Vent** | < 8 km/h = glassy (1,0) · offshore ≤ 30 km/h = 1,0 · side-shore 0,45-0,85 · onshore 0,85 si faible → 0,25 si > 20 km/h |

Le meilleur score de la journée donne le verdict :

| Score | Verdict |
|---|---|
| ≥ 8 | 🔥 IDÉAL — fonce ! |
| ≥ 6 | ✅ Bon — ça vaut le coup |
| ≥ 4 | 🤏 Surfable — longboard / mousse |
| ≥ 2 | 😐 Bof — si tu es en manque |
| < 2 | ❌ Flat / pas surfable |

Le **créneau** affiché est la plage horaire continue où le score reste ≥ 4 autour du meilleur moment.

## Utilisation au quotidien

Dans Telegram, conversation avec ton bot :

| Tu envoies | Kai répond |
|---|---|
| `surf`, `/surf`, `vagues`, `go`, `forecast` | Le forecast d'aujourd'hui et de demain |
| n'importe quoi d'autre | Un petit message d'aide |

Il n'y a **aucun envoi automatique** : pas de message tant que tu n'as rien demandé.
Le bot ne répond **qu'à ton compte** (`TELEGRAM_CHAT_ID`) ; les autres messages sont ignorés.

## Architecture

```
               Telegram ──"surf"──▶  https://palawai-surf.vercel.app/api/telegram
                   ▲                                │
                   │                                ▼
                   │                        surf_forecast/web.py
                   │                                │
                   │                                ▼
                   │            data.py ──2 requêtes──▶ Open-Meteo (houle + vent)
                   │                                │
                   │                    scoring.py → report.py (message)
                   └──────────── telegram.py ◀──────┘
```

```
.
├── _bmad/custom/agents/surf-forecaster/
│   ├── surf-forecaster.agent.yaml        # agent BMAD : persona, principes, menu
│   └── surf-forecaster-sidecar/
│       ├── spots.yaml                    # spots, conditions idéales, grille de notation
│       └── instructions.md               # méthode de prévision de l'agent
├── surf_forecast/
│   ├── data.py        # chargement de spots.yaml + appels Open-Meteo (avec nouvelles tentatives)
│   ├── scoring.py     # notation 0-10 par heure
│   ├── report.py      # construction du message Telegram (HTML)
│   ├── telegram.py    # appels à l'API Bot Telegram
│   ├── service.py     # forecast_text() / send_forecast() partagés
│   ├── web.py         # application WSGI : /api/telegram, /api/setup
│   └── __main__.py    # CLI : python -m surf_forecast [--dry-run]
├── app.py             # point d'entrée Vercel (expose surf_forecast.web.app)
├── vercel.json        # configuration Vercel (aucun cron)
├── tests/             # tests unitaires (unittest)
└── .github/workflows/daily-surf-forecast.yml   # envoi manuel de secours (GitHub Actions)
```

| Route | Rôle | Protection |
|---|---|---|
| `POST /api/telegram` | Webhook appelé par Telegram à chaque message | en-tête `X-Telegram-Bot-Api-Secret-Token` = `WEBHOOK_SECRET` + filtre sur `TELEGRAM_CHAT_ID` |
| `GET /api/setup?key=…` | Enregistre le webhook et la commande `/surf` auprès de Telegram | `key` = `WEBHOOK_SECRET` |

**Pourquoi Vercel plutôt que GitHub Actions ?** GitHub ne peut pas répondre à un message
Telegram ; Vercel héberge le webhook appelé par Telegram à chaque `surf`.

## Installation / réinstallation

Le guide pas à pas complet est dans **[docs/INSTALLATION.md](docs/INSTALLATION.md)** :

1. Créer le bot avec @BotFather et récupérer le token.
2. Récupérer ton chat id via `getUpdates`.
3. Créer le projet Vercel relié à ce dépôt.
4. Ajouter les 3 variables d'environnement.
5. Déployer, puis brancher le webhook avec `/api/setup`.

### Variables d'environnement (Vercel → Settings → Environment Variables)

| Variable | Contenu |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token donné par @BotFather |
| `TELEGRAM_CHAT_ID` | Ton chat id (plusieurs possibles, séparés par des virgules) |
| `WEBHOOK_SECRET` | Mot de passe aléatoire partagé avec Telegram |

⚠️ Ne jamais committer ces valeurs dans le dépôt.

## Personnaliser

| Je veux… | Où | Comment |
|---|---|---|
| Ajouter / retirer un spot | [`spots.yaml`](_bmad/custom/agents/surf-forecaster/surf-forecaster-sidecar/spots.yaml) | Copier un bloc `- id: …` et ajuster coordonnées, `swell_window`, `best_swell_dir`, `offshore_wind`, `best_height`. |
| Rendre la notation plus/moins sévère | `spots.yaml` → `criteria` | Seuils de période, de vent et de verdict. |
| Ajouter un mot déclencheur | [`surf_forecast/web.py`](surf_forecast/web.py) | Liste `TRIGGERS`. |
| Recevoir le forecast dans un groupe | Vercel | Ajouter le chat id du groupe (commence par `-`) à `TELEGRAM_CHAT_ID`, séparé par une virgule. |

Chaque push sur la branche de production redéploie automatiquement Vercel.

## Dépannage

| Symptôme | Cause probable | Solution |
|---|---|---|
| `surf` ne répond rien | Webhook non branché ou token changé | Rouvrir `https://palawai-surf.vercel.app/api/setup?key=<WEBHOOK_SECRET>` : la réponse doit contenir `"ok": true` et `last_error: null` |
| `/api/setup` renvoie `401` | Mauvaise `key` | Utiliser exactement la valeur de `WEBHOOK_SECRET` |
| `/api/setup` renvoie une erreur Telegram `401 Unauthorized` | Token invalide ou révoqué | Mettre le nouveau token dans Vercel, redéployer, rouvrir `/api/setup` |
| Erreur côté serveur | Exception dans la fonction | Vercel → projet → **Logs** |
| « 😕 Impossible de récupérer les prévisions » | Open-Meteo indisponible un instant | Renvoyer `surf` quelques minutes plus tard |
| Le bot répond par l'aide au lieu du forecast | Mot non reconnu | Envoyer exactement `surf` (majuscules acceptées) |
| Après un changement de variable, rien ne change | Les variables ne s'appliquent qu'aux nouveaux déploiements | Vercel → **Deployments** → ⋯ → **Redeploy** |

**Sécurité** : si le token du bot a fuité, envoie `/revoke` à @BotFather, mets le nouveau
token dans Vercel, redéploie, puis rouvre `/api/setup`.

## L'agent BMAD

Kai est défini dans
[`surf-forecaster.agent.yaml`](_bmad/custom/agents/surf-forecaster/surf-forecaster.agent.yaml)
(format BMAD v6, agent custom de type *expert* avec un sidecar de connaissances).

Pour l'utiliser dans un projet BMAD : installer BMAD (`npx bmad-method install`), ajouter le
dossier `_bmad/custom/agents/surf-forecaster` comme agent custom, activer **Kai**, puis :

| Commande | Action |
|---|---|
| `*forecast` | Forecast du jour et de demain (sans envoi) |
| `*send` | Envoyer le forecast sur Telegram maintenant |
| `*spots` | Guide des spots |
| `*conditions` | Conditions idéales et grille de notation |
| `*bot` | Utiliser le bot Telegram (« surf » à la demande) |

## Développement local

```bash
pip install -r requirements.txt
python -m surf_forecast --dry-run         # affiche le message sans l'envoyer
python -m unittest discover -s tests      # tests unitaires
```

Envoi réel depuis ta machine :

```bash
TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=yyy python -m surf_forecast
```

Le workflow GitHub **Surf forecast → Telegram (manuel)** fait la même chose depuis l'onglet
**Actions → Run workflow** (secrets `TELEGRAM_BOT_TOKEN` et `TELEGRAM_CHAT_ID` du dépôt).
