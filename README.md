# LinkedIn & X Auto Poster (Lambda)

Fetches tech/AI news from Reddit and X, generates one professional LinkedIn post and one concise X post using OpenAI (gpt-4o), posts them, and logs status to MongoDB. Designed to run as an AWS Lambda on a schedule via EventBridge.

## What it does
- Pulls items from:
  - Reddit (multiple tech/programming subreddits, keyword filtered)
  - X Recent Search (robust keyword trimming and fallback; rate-limit aware)
- Uses OpenAI to select the single most valuable item and generate:
  - LinkedIn post (professional, with Source: link and spaced hashtags)
  - X post (<= 280 chars + hashtags)
- Posts to LinkedIn (UGC API) and X (OAuth1 or OAuth2), once per trigger
- Stores post records and pending/retry state in MongoDB

## Repo structure (key files)
- `main.py`: single-run orchestrator (used by Lambda)
- `lambda_handler.py`: Lambda entrypoint calling `run_once()`
- `app/`
  - `config.py`: reads env and keywords
  - `fetch_reddit.py`, `fetch_x.py`: source fetchers
  - `generate.py`: OpenAI gpt-4o prompt/generation (one item)
  - `post_linkedin.py`, `post_x.py`: posting clients
  - `db_mongo.py`: MongoDB helpers (pending/posted records)
- `serverless.yml`: Serverless Framework config (Lambda + EventBridge schedules)

## Requirements
- Python 3.9+ locally (Lambda currently set to python3.9 in `serverless.yml`)
- AWS account + credentials configured for Serverless Framework
- OpenAI API key
- LinkedIn access token with permissions for UGC posts
- X API credentials:
  - Either OAuth1 keys with write permissions (read+write)
  - Or an OAuth2 user access token with `tweet.write` scope
- MongoDB (Atlas or DocumentDB or local)

## Environment variables
Required (match `serverless.yml`):
- `OPENAI_API_KEY`
- `LINKEDIN_ACCESS_TOKEN`
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`
- `X_BEARER_TOKEN` (for search)
- One of (for posting to X):
  - OAuth1: `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`
  - OAuth2: `X_CLIENT_ID`, `X_CLIENT_SECRET` (to mint tokens externally), and `X_OAUTH2_ACCESS_TOKEN` for posting
- MongoDB: `MONGO_URI`, `MONGO_DB` (default `autoposter`), `MONGO_COLLECTION` (default `posts`)

Optional/unused by core flow (may be present in `serverless.yml`): `LINKEDIN_ID_TOKEN`, `LINKEDIN_CLIENTID`, `LINKEDIN_SECRETID`, Discord vars.

## Local test
Install dependencies and run one cycle locally:
```bash
pip install -r requirements.txt
python lambda_handler.py
```
This prints `{"status": "ok"}` and executes a full run.

## Deploy with Serverless Framework
1. Ensure Serverless is installed and AWS credentials are set.
2. Place your environment variables in a local `.env` (the config uses `useDotenv: true`).
3. Install plugins:
```bash
sls plugin install -n serverless-python-requirements
sls plugin install -n serverless-dotenv-plugin
```
4. Deploy:
```bash
sls deploy
```
5. Invoke once to test:
```bash
sls invoke -f autoposter
```

### Scheduling
- `serverless.yml` defines two EventBridge schedules (UTC). Adjust `rate: cron(...)` or remove the `events` block if you prefer manual invocation.
- Region defaults to `ap-south-1`; change `provider.region` as needed.

## serverless.yml explained (concise)
- **service/frameworkVersion**: project name and Serverless v3.
- **useDotenv: true**: loads `.env` into `provider.environment` for deploys.
- **provider**:
  - **runtime**: Python runtime for Lambda (python3.9 set here).
  - **region/stage**: AWS region and stage; change region to where you deploy.
  - **memorySize/timeout**: Lambda resources (adjust if needed).
  - **environment**: all env vars your function reads (OpenAI, LinkedIn, X, Mongo, etc.).
- **plugins**:
  - `serverless-python-requirements`: builds Python deps into the bundle (uses Docker if `dockerizePip: true`).
  - `serverless-dotenv-plugin`: injects `.env` into env variables at deploy time.
- **custom.pythonRequirements**:
  - **dockerizePip**: set `true` for native wheels compatibility; `false` uses local pip.
  - **slim/strip**: reduce package size by removing extraneous files.
- **package.patterns**: include everything except caches/dist-info/pyc and old sqlite file.
- **functions.autoposter**:
  - **handler**: entry is `lambda_handler.handler`.
  - **events.schedule**: two EventBridge cron triggers in UTC; set `enabled: true/false` or edit the cron to change run times.

## Notes and tips
- X rate limits: The fetcher trims keywords and retries with a minimal set. If you still hit limits or see 403, reduce keyword breadth or ensure your app has appropriate access.
- LinkedIn posts with URLs are sent as ARTICLE shares with `originalUrl` and DataMap-wrapped `title`.
- MongoDB is used to avoid reposts and to retry pending items automatically on next run.
- Keywords/subreddits are broad by default; override via `KEYWORDS` env if desired.

## Security
- Do not commit secrets. Use `.env` locally and set environment variables in Lambda/Serverless for production.
- Consider AWS Secrets Manager/SSM for managing sensitive values.
