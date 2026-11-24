# Permissions prerequisite

The skills run a lot of small commands (inspecting packages, linting, running AutoPkg, reading PRs). Without allow rules, Claude Code prompts for each one. Add the rules below once and the routine work runs without interruption. Committing, pushing, creating PRs, Jira writes and production access still prompt.

## Where to put them

- **`.claude/settings.local.json`** in your clone: personal and per-repo.
- **`~/.claude/settings.json`**: applies to every project.

Merge the `allow` entries into an existing `permissions.allow` array rather than replacing the file. Read the list first: you are approving these commands for every session.

## Baseline allow list

```json
{
  "permissions": {
    "allow": [
      "Bash(autopkg run *)",
      "Bash(autopkg search *)",
      "Bash(autopkg info *)",
      "Bash(/usr/local/autopkg/python \"*AutoPkg Linters/autopkg-linter.py\" *)",
      "Bash(plutil -p *)",
      "Bash(plutil -lint *)",
      "Bash(defaults read *)",
      "Bash(codesign -d *)",
      "Bash(codesign --display *)",
      "Bash(pkgutil --expand *)",
      "Bash(pkgutil --pkgs *)",
      "Bash(pkgutil --payload-files *)",
      "Bash(lsbom *)",
      "Bash(hdiutil attach *)",
      "Bash(hdiutil detach *)",
      "Bash(git status *)",
      "Bash(git log *)",
      "Bash(git show *)",
      "Bash(git branch --list *)",
      "Bash(git diff)",
      "Bash(git diff origin/main...HEAD)",
      "Bash(git diff origin/master...HEAD)",
      "Bash(git diff --stat *)",
      "Bash(git diff --name-only *)",
      "Bash(gh pr view *)",
      "Bash(gh pr list *)",
      "Bash(gh pr diff *)",
      "Bash(gh pr checks *)",
      "Bash(gh run list *)",
      "Bash(gh run view *)",
      "Bash(curl -s \"https://raw.githubusercontent.com/autopkg/index/main/v1/index.json\" -o /tmp/autopkg-index.json)",
      "Read(//tmp/autopkg-index.json)",
      "Read(~/Library/AutoPkg/**)",
      "WebFetch(domain:github.com)",
      "WebFetch(domain:raw.githubusercontent.com)",
      "WebFetch(domain:api.github.com)",
      "WebFetch(domain:support.apple.com)",
      "WebFetch(domain:learn.jamf.com)"
    ]
  }
}
```

What each group is for:

| Rules | Used by |
| --- | --- |
| `autopkg run/search/info` | Running and testing recipes, checking for existing recipes |
| `autopkg-linter.py` | The mandatory lint step. The rule matches the quoted form the skill runs (`python "*AutoPkg Linters/autopkg-linter.py" --all ...`) |
| `plutil -p/-lint`, `defaults read`, `codesign -d`, `pkgutil`, `lsbom`, `hdiutil` | Inspecting downloaded apps and packages (Info.plist, signing requirements, payloads) |
| `git` read forms, `gh pr view/list/diff/checks`, `gh run` | Reviewing branches, PRs and CI |
| `curl ... index.json` | The AutoPkg index lookup that gates recipe creation (exact command from the skill) |
| `Read(...)`, `WebFetch(...)` | The downloaded index file, the AutoPkg cache, and vendor/docs lookups. Add `Read(~/Downloads/**)` yourself only if you inspect downloads there |

Bash rules use prefix matching with `*`. The relative paths in rules only match when Claude runs from the repo root. If your install path differs (for example the linter folder), adjust that rule. Make sure `.claude/settings.local.json` is git-ignored so you don't commit your settings.

## These rules are not all read-only

Know what you are approving:

- **`autopkg run *`** executes a recipe's processors and any embedded scripts, and downloads from the recipe's URLs. Only keep this rule if you run recipes you have reviewed. For unreviewed recipes, delete it and approve each run.
- **`pkgutil --expand`** writes the expanded package to the directory you give it; **`hdiutil attach`** mounts a disk image from a download. Both act on untrusted files by design.
- **`plutil -p/-lint`** and **`git branch --list`** are the read-only forms; `plutil -replace/-insert` and `git branch -D` are deliberately not matched. `git log *` and `git show *` still accept options such as `--output=<file>`, which writes a file: keep that in mind or drop the rule.

## Deliberately not in the list

Do not add these, even though they save prompts. Each lets a mistaken or prompt-injected command act without you seeing it:

- `Bash(ssh *)` or `Bash(scp *)`: would auto-approve writes to production.
- `Bash(security find-generic-password *)`, `Bash(security find-internet-password *)`: reads secrets out of your Keychain.
- `Bash(env)`, `Bash(curl *)`, `Bash(python3 *)`, `Bash(zsh -c *)`, `Bash(sh -c *)`: arbitrary execution or exfiltration.
- `Read(//Users/<you>/**)` or `Read(~/**)`: your whole home folder, including SSH keys and credentials.
- `Bash(gh pr create*)`, `Bash(git push*)`, `Bash(git commit*)`: outward-facing. Approve these each time.
- Any rule containing a token or password. If a command needs `SONAR_TOKEN=...`, an API token or similar, keep it in your Keychain or environment: rule text is stored in plain text.

Check your own settings for the last case: `grep -nE 'token|TOKEN|squ_|ghp_|password' ~/.claude/settings*.json .claude/settings*.json`.
