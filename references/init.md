# Environment Initialization

Use these Agent instructions to check and prepare the environment required to
run AutoFlow and the selected module. This document is client-neutral: run the
commands from the installed Skill root, regardless of the host Agent client.
Workspace layout and execution-mode setup belong in `SKILL.md`.

```bash
python --version
python -m pip --version
git --version
node --version
```

Install only the missing dependencies required by the selected module, then
repeat its check. From the Skill root, install AutoFlow's Python dependencies
with:

```bash
python -m pip install -r requirements.txt
```

| Need | Check | Install when missing |
|---|---|---|
| Git for task research/build | `git --version` | Use the host package manager, for example `winget install --id Git.Git -e`, `brew install git`, or `sudo apt-get install git`. |
| Node tooling | `node --version` | Use the host package manager, for example `winget install --id OpenJS.NodeJS.LTS -e`, `brew install node`, or `sudo apt-get install nodejs npm`. |
| Browser capture | `python -c "import playwright"` | `python -m pip install playwright`, then `python -m playwright install chromium`. If the browser is not on `PATH`, set `AUTOFLOW_BROWSER_PATH` to its executable. |
| Mermaid diagrams | `mmdc --version` | `npm install -g @mermaid-js/mermaid-cli` |
| D2 diagrams | `d2 --version` | Install D2 with the host package manager or the official D2 installer. |
| Office documents | `officecli --version` | Follow the platform-specific installer in `integrations/officecli/SKILL.md`. |
| Video processing | `ffmpeg -version` | Use the host package manager, for example `winget install --id Gyan.FFmpeg -e`, `brew install ffmpeg`, or `sudo apt-get install ffmpeg`. |

Do not create image API credentials or invent values for `BASEURL` or `APIKEY`.
An unavailable AI-image route remains blocked until the user supplies valid
credentials.
