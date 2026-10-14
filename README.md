# ORGOS Stack

Open WebUI (co-branded) + vLLM + Postgres/pgvector. Runs on-prem or in the customer's cloud; no data leaves the host.

## Quick start

```bash
cp .env.example .env   # fill in secrets: openssl rand -hex 32
```

GPU server (NVIDIA + nvidia-container-toolkit):

```bash
docker compose --profile gpu up -d
```

Mac / dev (no NVIDIA): run Ollama natively, set `OPENAI_API_BASE_URL` in `.env`, then:

```bash
docker compose up -d
```

Open http://localhost:3000 — the first account created becomes admin.

## Integration tests (CPU, no GPU needed)

```bash
scripts/test-integration.sh          # up → pull small model → pytest → down
scripts/test-integration.sh --keep   # leave the stack running afterwards
```

Uses `.env.ci` (test values only) and the `cpu` profile: Ollama with `qwen3:1.7b`. Tests cover health, model listing, chat, and RAG (upload a document, check the answer comes from it). Runs on GitHub Actions (`.github/workflows/integration.yml`) and in Claude Code cloud sessions.

**Claude Code cloud environment:** setup script `bash scripts/cloud-setup.sh`; network level *Custom* (keep the default package-manager list) and add `huggingface.co`, `*.huggingface.co`, `*.hf.co`, `ollama.com`, `registry.ollama.ai`, plus any model-download CDN host that shows up as denied.

## Turn it into a product (in the admin UI)

1. **Assistants** — Workspace → Models: create "HR Policy Assistant", "Contract Reviewer", etc. on top of `orgos-default` with a system prompt, attached knowledge, and group access.
2. **Knowledge** — Workspace → Knowledge: upload documents per team; restrict each collection to a group.
3. **Users & groups** — Admin → Users: approve pending users, create groups (e.g. Legal, HR), assign assistants/knowledge per group.
4. **SSO** — add OIDC env vars (Entra ID / Google) to replace local passwords.

## Branding

The Open WebUI license requires its name/logo to remain visible; `WEBUI_NAME` sets the co-brand. Do not remove Open WebUI attribution without an enterprise license.

## Not yet built (ORGOS proprietary layer)

- Gateway: audit log, policy, PII redaction (sits between Open WebUI and vLLM)
- Connectors with permission sync (SharePoint, Google Drive, NAS)
- Fleet agent: installs, signed updates, health (no customer data)
