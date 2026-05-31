# Publish checklist (deferred)

Use this when you are ready to push the portfolio to GitHub and LinkedIn.

## Before push

- [ ] Confirm `.env` is **not** tracked (`git status` — should be ignored)
- [ ] Run `uv run pytest` — all green
- [ ] Run `.\scripts\bootstrap_demo.ps1` — Grafana panels populated
- [ ] Run `uv run finops-report-results` — verify [data/RESULTS.md](../data/RESULTS.md) matches JSON

## Create public repo

```powershell
git init
git add .
git commit -m "FinOps AI Gateway — observable cost-routing RAG demo"
gh repo create finops-ai-gateway --public --source=. --push
```

Or push to an existing remote:

```powershell
git remote add origin https://github.com/<you>/finops-ai-gateway.git
git push -u origin main
```

## Pin on GitHub profile

1. GitHub → your profile → **Customize your pins**
2. Pin **finops-ai-gateway**

## LinkedIn

Copy text from [LINKEDIN_POST.md](LINKEDIN_POST.md). Attach `docs/images/grafana-cost-by-tier.png`.

Suggested headline finding:

> 58% of queries routed to local Ollama; hybrid RAG +0.19 context_precision on an 8-pair pilot. Grafana cost is simulated (actual spend $0 in demo mode).

## Blog

Publish [BLOG_DRAFT.md](BLOG_DRAFT.md) on Dev.to, Medium, or your site. Link the repo and architecture diagram.
