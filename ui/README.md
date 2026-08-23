# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend enabling type-aware lint rules by installing `oxlint-tsgolint` and editing `.oxlintrc.json`:

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "typescript", "oxc"],
  "options": {
    "typeAware": true
  },
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }]
  }
}
```

See the [Oxlint rules documentation](https://oxc.rs/docs/guide/usage/linter/rules) for the full list of rules and categories.



1. Prepare the database
Open the Supabase project → SQL Editor.
Run supabase/migrations/001_couponfinder.sql.
Copy the pooler connection string (port 6543, not the direct 5432 URL).
2. Create the Vercel project
Push this repo to GitHub (or GitLab/Bitbucket).
In Vercel: Add New… → Project and import that repo.
Root directory: repository root (not ui/). vercel.json already sets:
build: npm --prefix ui run build
output: ui/dist
Python functions: api/*.py with src/** bundled
Do not set a custom output directory in the dashboard that overrides vercel.json.
3. Environment variables
In Project → Settings → Environment Variables, add for Production (and Preview if you use it):

Name	Value
DATABASE_URL
Supabase pooler URL (…:6543/postgres)
DB_SCHEMA
coupons
DB_TABLE
gc_coupons
ADMIN_API_TOKEN
a long random secret
ALLOWED_COUPON_HOSTS
offers.greatclips.com
Keep DATABASE_URL and ADMIN_API_TOKEN out of config.ini and out of any VITE_* frontend vars.

Python functions need packages at deploy time. Vercel installs from a root requirements.txt. If you do not have one yet, add:

requests>=2.31
beautifulsoup4>=4.12
psycopg[binary]>=3.2
Then redeploy.

4. Deploy
Click Deploy. After it succeeds, open the production URL.

Public offers: / → /api/offers
Admin: Admin tab → /api/fetch-coupons (sends X-Admin-Token)
5. Load coupons
Open Admin on the live site.
Paste ADMIN_API_TOKEN.
Paste allowed HTTPS URLs (up to 10).
Fetch Coupons.
Deployed fetch uses raw HTML only. Playwright rendering does not run on Vercel, so codes that appear only after JS or a redemption click may be missing. For those, run `python -m couponfinder.admin_api` with render enabled, then refresh the live UI.

6. Local check (optional)
From the repo root:

npx vercel dev
Put the same variables in a root .env (see .env.example). Do not use files/urls.txt for the deployed app; paste URLs in Admin.