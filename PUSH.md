# PUSH — create the private repo and upload

This folder is already a git repo with full history. You only need to create
the remote and push.

## Option A — GitHub CLI (recommended, mobile-friendly)
```bash
gh auth login    # GitHub.com → HTTPS → "Login with a web browser" (device code)
gh repo create gcp-healthcare-foundation --private --source=. --remote=origin --push
```
For an org: `gh repo create <org>/gcp-healthcare-foundation --private --source=. --push`

## Option B — plain git (create empty repo in the GitHub app first)
1. In GitHub (web/app): New repo → name `gcp-healthcare-foundation` → **Private** →
   do NOT add README/.gitignore/license → Create.
2. Then:
```bash
git remote add origin https://github.com/<your-username>/gcp-healthcare-foundation.git
git push -u origin main
```
When prompted for a password, paste a **Personal Access Token** (classic: `repo`
scope, or fine-grained: Contents read/write). Entered locally on your device only.

## Optional: put your real identity on the commits
```bash
git config user.name  "Your Name"
git config user.email "you@example.com"
git commit --amend --reset-author -m "GCP healthcare foundation"
```

## Safe to push?
Yes — `.gitignore` excludes all state and real `*.tfvars`; only `*.tfvars.example`
templates are tracked. Verify anytime with: `git ls-files | grep tfvars`
(should show only `.example` files).
