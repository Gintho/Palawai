# Installation pas à pas

Ce guide permet de (ré)installer le bot de zéro : bot Telegram → projet Vercel → webhook.
Compte environ 15 minutes.

---

## 1. Créer le bot Telegram

1. Dans Telegram, cherche **@BotFather** (badge bleu ✔️) et appuie sur **Démarrer**.
2. Envoie `/newbot`.
3. Donne un **nom** affiché (ex. `Kai Surf Palavas`), puis un **identifiant** qui finit par
   `bot` (ex. `kai_surf_palavas_bot`).
4. BotFather répond avec un **token** du type `7412345678:AAH3kX9...zQw`.
   Garde-le secret : il permet d'écrire au nom du bot.

## 2. Récupérer ton chat id

1. Ouvre la conversation avec **ton bot** (lien `t.me/…` donné par BotFather) et appuie sur
   **Démarrer**, puis envoie un message (ex. `salut`).
2. Dans un navigateur, ouvre (en remplaçant `TOKEN`, **sans** `< >`) :
   ```
   https://api.telegram.org/botTOKEN/getUpdates
   ```
3. Repère `"chat":{"id":123456789,...}` : ce nombre est ton **chat id**.

> Résultat vide (`"result": []`) ? Tu n'as pas encore écrit au bot, ou pas au bon :
> vérifie son nom avec `https://api.telegram.org/botTOKEN/getMe`, écris-lui, recharge.
>
> Pour un **groupe** : ajoute le bot au groupe, écris dans le groupe, relis `getUpdates`.
> Le chat id d'un groupe commence par `-` (garde le `-`).

⚠️ Si un webhook est déjà branché, `getUpdates` renvoie une erreur `409 Conflict`.
C'est normal une fois le bot installé : le chat id ne change pas, réutilise l'ancien.

## 3. Créer le projet Vercel

1. Va sur **https://vercel.com**, connecte-toi avec ton compte GitHub.
2. En haut à gauche, choisis l'équipe (ici **Gintho's projects**).
3. **Add New… → Project**, choisis le dépôt **Gintho/Palawai** → **Import**.
4. Laisse les réglages par défaut (Vercel détecte Python) et clique sur **Deploy**.
   Le premier déploiement peut échouer faute de variables : ce n'est pas grave.

Projet actuel : **`palawai-surf`** → https://palawai-surf.vercel.app

### Protection des déploiements

Telegram doit pouvoir appeler l'URL de production sans être connecté à Vercel :
**Settings → Deployment Protection → Vercel Authentication** doit être sur
**Standard Protection** (seules les versions de test sont protégées), pas sur « All Deployments ».

## 4. Ajouter les variables d'environnement

1. Dans le projet : **Settings** → **Environment Variables** (menu de gauche).
2. Ajoute ces 3 variables (bouton **Add Another** entre chaque), environnement
   **Production** coché :

   | Key | Value |
   |---|---|
   | `TELEGRAM_BOT_TOKEN` | le token de l'étape 1 |
   | `TELEGRAM_CHAT_ID` | le chat id de l'étape 2 |
   | `WEBHOOK_SECRET` | un mot de passe aléatoire |

3. **Save**.

Pour générer le mot de passe :

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

> Astuce : tu peux coller d'un coup `CLE=valeur` sur 3 lignes dans le champ **Key**,
> Vercel remplit tout seul les couples.

## 5. Déployer

Les variables ne s'appliquent qu'aux **nouveaux** déploiements :
**Deployments** → dernier déploiement → **⋯** → **Redeploy**.
(Chaque push sur la branche de production redéploie aussi automatiquement.)

Vérifie que https://palawai-surf.vercel.app répond `{"ok": true, "service": "Kai surf forecast"}`.

## 6. Brancher le webhook Telegram

Ouvre dans le navigateur (remplace par ta valeur de `WEBHOOK_SECRET`) :

```
https://palawai-surf.vercel.app/api/setup?key=WEBHOOK_SECRET
```

Réponse attendue :

```json
{"ok": true, "webhook_url": "https://palawai-surf.vercel.app/api/telegram", "pending": 0, "last_error": null}
```

Cette étape enregistre aussi la commande `/surf` dans le menu du bot.
À refaire **à chaque changement de token** ou de `WEBHOOK_SECRET`.

## 7. Tester

Envoie **`surf`** au bot : il affiche « en train d'écrire… » puis le forecast arrive.

Il n'y a pas d'envoi automatique : le bot n'écrit que lorsque tu lui envoies `surf`.

---

## Changer de token (fuite, régénération)

1. @BotFather → `/revoke` → choisis le bot → nouveau token.
2. Vercel → **Settings → Environment Variables** → modifie `TELEGRAM_BOT_TOKEN`.
3. **Redeploy**.
4. Rouvre `/api/setup?key=…` (étape 6).
5. Si tu utilises le workflow GitHub manuel : mets aussi à jour le secret
   `TELEGRAM_BOT_TOKEN` dans **GitHub → Settings → Secrets and variables → Actions**.
