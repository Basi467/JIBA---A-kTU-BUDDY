# Deploying JIBA to Render

Two Docker services (`api`, `frontend`) sharing a repo — deployed as two
separate Render Web Services from the existing `api/Dockerfile` and
`frontend/Dockerfile`. Render's free tier ($0/mo) is used here: the
container's disk is ephemeral (wiped on every deploy/restart), which is
fine for this app — `database/ktu.db` is baked into the image with real
seeded demo data, so a restart just means the DB resets to that seed
instead of losing anything meaningful. If you outgrow that later, Render's
paid tiers add a persistent Disk you can mount at `/app/data` (see the
`KTU_DB_PATH` env var below).

Manual dashboard steps below, not a `render.yaml` blueprint — the frontend
needs the backend's *actual* assigned URL baked in at build time (Vite
inlines env vars into the static bundle), which is easier to get right by
deploying the API first and copying its real URL than by trying to wire
cross-service references in a blueprint file sight-unseen.

## 1. Push this repo to GitHub

```bash
gh repo create jiba-ktu-buddy --private --source=. --remote=origin --push
```

(Or manually: create an empty repo on github.com, then `git remote add
origin <url> && git push -u origin master`.)

## 2. Deploy the API

On [render.com](https://render.com) (sign up free, no card required for
the free tier):

1. **New +** → **Web Service** → connect your GitHub account → select this repo.
2. **Root Directory**: leave blank (repo root — the Dockerfile itself lives in `api/`).
3. **Dockerfile Path**: `api/Dockerfile`
4. **Instance Type**: Free
5. **Environment Variables** — add these (Settings → Environment):
   | Key | Value |
   |---|---|
   | `OPENAI_API_KEY` | your real key from `.env` |
   | `CORS_ALLOWED_ORIGINS` | leave blank for now — you'll set this after step 3 |
   | `SENDGRID_API_KEY` | your key, once you have one (optional — degrades gracefully without it) |
   | `SENDGRID_FROM_EMAIL` | your verified sender, once you have one |
   | `FRONTEND_BASE_URL` | leave blank for now |
   | `SENTRY_DSN` | your backend DSN, once you have one (optional) |
6. **Create Web Service**. First build takes a few minutes. Once live, copy its URL — something like `https://jiba-api.onrender.com`.

## 3. Deploy the frontend

1. **New +** → **Web Service** → same repo.
2. **Root Directory**: `frontend`
3. **Dockerfile Path**: `frontend/Dockerfile`
4. **Instance Type**: Free
5. **Environment Variables** (these are Docker *build args* — Render passes env vars set here into the build):
   | Key | Value |
   |---|---|
   | `VITE_API_BASE_URL` | the API URL from step 2, e.g. `https://jiba-api.onrender.com` |
   | `VITE_SENTRY_DSN` | your frontend DSN, once you have one (optional) |
6. **Create Web Service**. Once live, copy its URL — e.g. `https://jiba-frontend.onrender.com`.

## 4. Wire the two together

Go back to the **api** service's Environment tab and set the two values you skipped:

- `CORS_ALLOWED_ORIGINS` = the frontend URL from step 3 (e.g. `https://jiba-frontend.onrender.com`)
- `FRONTEND_BASE_URL` = the same frontend URL (used to build password-reset links)

Save — this triggers an automatic redeploy of the API. Once it's back up, open the frontend URL and confirm login works end to end.

## 5. (Optional) Custom domain

If you own a domain: on either service, Settings → Custom Domains → add
yours, then create the CNAME record it gives you with your domain
registrar. Free on Render, takes a few minutes to propagate.

## Free-tier quirks to know about

- **Cold starts**: free services spin down after 15 minutes idle and take ~30-60s to wake on the next request. Fine for a resume demo; mention it if you're walking someone through it live.
- **Data resets**: as above — every redeploy/restart resets the DB to the baked-in seed (real demo data, not empty).
- **Redeploy on push**: Render auto-deploys on every push to your default branch once connected — no extra CI config needed.
