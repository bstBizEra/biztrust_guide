# Live Preview & Publishing Runbook

**Document:** BIZTRUST-GUIDE-RUNBOOK-001  
**Applies to:** `bstBizEra/biztrust_guide`  
**Production URL:** `https://bstbizera.github.io/biztrust_guide/` — published by `.github/workflows/pages.yml`. Whether it currently serves the `main` head is not recorded here: read it from the Pages workflow runs and the `github-pages` deployments, as `README.md` § *Current delivery state* describes. An earlier version of this line said Pages had never been activated; it was written five minutes after the first deployment succeeded and stood for a day (issue #66).

## 1. Choose the correct preview mode

| Need | Use | Persistence | Audience |
|---|---|---:|---|
| Review files on your own computer | Python local server | Until terminal closes | Your device only by default |
| Share a stable public link | GitHub Pages | Persistent | Public internet |
| Review an unmerged change | Pull request + local checkout | Per branch | Reviewers with repository access |

Do not use Python `http.server` as a public or production service. Python documents it as a basic local server with limited security checks.

## 2. Publish with GitHub Pages — recommended path

This repository contains `.github/workflows/pages.yml`, which deploys the static files from the repository root.

### One-time repository configuration

1. Open `https://github.com/bstBizEra/biztrust_guide`.
2. Select **Settings**.
3. In **Code, planning, and automation**, select **Pages**.
4. Under **Build and deployment**, set **Source** to **GitHub Actions**.
5. Open the **Actions** tab.
6. Open the **Deploy BizTrust Guide to GitHub Pages** workflow.
7. If no run exists, select **Run workflow → main → Run workflow**.
8. Wait for both `validate` and `deploy` to become green.
9. Return to **Settings → Pages** and select **Visit site**.

Expected URL:

```text
https://bstbizera.github.io/biztrust_guide/
```

GitHub notes that initial publication or updates can take several minutes.

**The Actions run is a convenience pointer, not the deployment record.** From 1 October 2026
GitHub's Actions retention setting covers checks, workflow runs and statuses, defaulting to 90
days. A `workflow_run` URL recorded as evidence therefore stops resolving roughly three months
after it is written, and an evidence record whose only citation has expired proves nothing.

The durable record is the pair **`source_commit` + what the live URL actually serves**, because
git objects and the deployed bytes both outlive the run that produced them. Verify a deployment
by comparing them directly rather than by opening a run:

```bash
# what the live site serves, vs what the commit says it should
curl -sS https://bstbizera.github.io/biztrust_guide/index.html | wc -c
git show <source_commit>:index.html | wc -c
curl -sS https://bstbizera.github.io/biztrust_guide/index.html | sha256sum
git show <source_commit>:index.html | sha256sum
```

Compare **byte counts first, then the SHA-256 of the same bytes**. A bare hash carries no
algorithm and no length, so two digests from different tools look like two different files;
the byte count discriminates on its own and makes the comparison checkable by a reader who
has neither tool to hand.

**Pipe directly; do not stage the response in a shell variable.** `$(curl ...)` strips
trailing newlines, so `printf '%s' "$LIVE" | wc -c` reports one byte short of the file and the
two SHA-256 values then disagree — a mismatch that is an artifact of the harness, not of the
deployment. This was observed while writing this section: the variable form reported 39226
against a source of 39227, and the piped form reported 39227 on both sides for the same commit.
A verification procedure that can produce a confident false negative is worse than none.

### Every later update

```text
feature branch
  → pull request
  → validation passes
  → approved merge to main
  → Pages workflow
  → github-pages environment
  → live site
```

Do not edit deployed files manually. The repository commit is the source of truth.

## 3. Alternative: deploy directly from `main`

Because this is plain HTML/CSS/JavaScript, GitHub Pages can also publish directly from the branch:

1. Open **Settings → Pages**.
2. Under **Source**, choose **Deploy from a branch**.
3. Select branch **main**.
4. Select folder **/(root)**.
5. Select **Save**.

Use only one Pages source. The included Actions workflow is recommended because it validates continuity and assets before deployment and leaves an explicit deployment record.

## 4. Local preview with Python

### Prerequisites

Confirm Git and Python:

```bash
git --version
python3 --version
```

On Windows PowerShell:

```powershell
git --version
py --version
```

### First-time setup — Linux, macOS or WSL

```bash
git clone https://github.com/bstBizEra/biztrust_guide.git
cd biztrust_guide
python3 -m http.server 8080 --bind 127.0.0.1
```

Open:

```text
http://127.0.0.1:8080/
```

### First-time setup — Windows PowerShell

```powershell
git clone https://github.com/bstBizEra/biztrust_guide.git
Set-Location biztrust_guide
py -m http.server 8080 --bind 127.0.0.1
```

Open `http://127.0.0.1:8080/`.

### Preview without changing directory

Linux, macOS or WSL:

```bash
python3 -m http.server 8080 --bind 127.0.0.1 --directory /path/to/biztrust_guide
```

Windows PowerShell:

```powershell
py -m http.server 8080 --bind 127.0.0.1 --directory C:\path\to\biztrust_guide
```

### Stop the server

Return to the terminal and press:

```text
Ctrl+C
```

### Refresh after editing

Files are served from disk. Save the file and refresh the browser. Use a hard refresh when CSS or JavaScript appears cached:

- Windows/Linux: `Ctrl+Shift+R`
- macOS: `Command+Shift+R`

## 5. Troubleshooting

### `python3: command not found`

- Windows: try `py` or `python`.
- Ubuntu/WSL: install Python through the approved system package process.
- macOS: use the installed Python 3 command or your managed development environment.

### `Address already in use`

Use another unprivileged port:

```bash
python3 -m http.server 8081 --bind 127.0.0.1
```

Then open `http://127.0.0.1:8081/`.

### Browser shows a directory listing

The server was started from the wrong folder. Verify:

```bash
pwd
ls index.html
```

Start from the repository root or use `--directory`.

### CSS, JavaScript or images return 404

1. Check capitalization; GitHub Pages paths are case-sensitive.
2. Confirm `styles.css`, `script.js` and `assets/` resolve **from the page's own directory** — beside `index.html` at the root, and one level up (`../styles.css`) from any page in `stages/`.
3. Use relative links such as `assets/unitrust-icon.png`.
4. Run `python3 scripts/validate_continuity.py`.

### GitHub Pages returns 404

1. Confirm Pages source is **GitHub Actions** if using the included workflow.
2. Confirm the latest Pages workflow completed successfully.
3. Confirm root-level `index.html` exists on `main`.
4. Use the project-site URL including `/biztrust_guide/`.
5. Allow several minutes for first publication.

### Workflow does not deploy

Check that the workflow has:

- `contents: read`;
- `pages: write`;
- `id-token: write`;
- a `github-pages` environment;
- a successful uploaded Pages artifact;
- no competing Pages deployment already running.

## 6. Security boundaries

- Bind local preview to `127.0.0.1`; Python otherwise binds to all interfaces by default.
- Do not preview from a folder containing secrets or unrelated sensitive files.
- The Python handler maps URLs to files below the served directory and follows symbolic links.
- GitHub Pages is public; never commit private client, policy, claim, payment or credential data.
- Enforce HTTPS in GitHub Pages settings.

## 7. Verification evidence

Before reporting a preview or deployment as successful, record:

```text
source_commit: <40-character SHA>
preview_mode: local | github-pages
url: <tested URL>
entry_file: index.html
assets_checked: true
validation_command: python3 scripts/validate_continuity.py
validation_exit_code: 0
workflow_run: <URL or not-applicable>          # expires ~90 days; pointer only
deployed_bytes: <byte count of the fetched entry_file>
deployed_sha256: <sha256 of the same bytes>
source_bytes: <byte count of git show <source_commit>:index.html>
source_sha256: <sha256 of the same bytes>
verified_by: <role>
verified_at: <RFC3339 timestamp>
```

## References

- [Configuring a GitHub Pages publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [Using custom workflows with GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [Troubleshooting GitHub Pages 404 errors](https://docs.github.com/en/pages/getting-started-with-github-pages/troubleshooting-404-errors-for-github-pages-sites)
- [Securing GitHub Pages with HTTPS](https://docs.github.com/en/pages/getting-started-with-github-pages/securing-your-github-pages-site-with-https)
- [Python `http.server`](https://docs.python.org/3/library/http.server.html)

