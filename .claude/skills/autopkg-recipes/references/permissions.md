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
      "Bash(gh pr view *)",
      "Bash(gh pr list *)",
      "Bash(gh pr diff *)",
      "Bash(gh pr checks *)",
      "Bash(gh run list *)",
      "Bash(gh run view *)",
      "Bash(curl -s \"https://raw.githubusercontent.com/autopkg/index/main/v1/index.json\" -o /tmp/autopkg-index.json)",
      "Read(//tmp/autopkg-index.json)",
      "Read(~/Library/AutoPkg/Cache/**)",
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
| `gh pr view/list/diff/checks`, `gh run` | Reviewing PRs and CI |
| `curl ... index.json` | The AutoPkg index lookup that gates recipe creation (exact command from the skill) |
| `Read(...)`, `WebFetch(...)` | The downloaded index file, the AutoPkg cache, and vendor/docs lookups. Add `Read(~/Downloads/**)` yourself only if you inspect downloads there |

Bash rules use prefix matching with `*`. Commands must be run as written, from the repo root, to match: absolute paths and worktrees prompt, and only `/usr/local/autopkg/python` is install-specific. The lint step in SKILL.md is `root=$(...)` then `cd` then the linter call; whether that form matches the linter rule has not been tested, so if it prompts, approve it once. Make sure `.claude/settings.local.json` is git-ignored so you don't commit your settings.

## These rules are not all read-only

Know what you are approving:

- **`autopkg run *`** executes a recipe's processors and any embedded scripts, and downloads from the recipe's URLs. Only keep this rule if you run recipes you have reviewed. For unreviewed recipes, delete it and approve each run.
- **`pkgutil --expand`** writes the expanded package to the directory you give it; **`hdiutil attach`** mounts a disk image from a download. Both act on untrusted files by design.
- **The linter rule** runs `autopkg-linter.py`, whose linters rewrite and move files. Run it on one recipe folder, never the repo root, and review `git diff` afterwards. The leading `*` in the rule is a wildcard that also absorbs the literal `*` in the `*AutoPkg Linters` folder name, so it matches a linter at any path: only keep it if you trust the repo you open.
- **`plutil -p/-lint`** are the read-only forms; `plutil -replace/-insert` is deliberately not matched.
- **Git:** read-only `git status`, `diff`, `log` and `show` are normally auto-approved by Claude Code, so there are no rules for them. If you are prompted for them, add your own rule and remember options such as `--output=<file>` write files.
- **Bash index reads:** only the Read tool is covered for `/tmp/autopkg-index.json`. The skill's `python3` step that reads it, and inspecting the expanded package under `/tmp` (for example `/tmp/expanded_pkg`) with the Read tool, still prompt: `python3` is deliberately not allowed.

## Deliberately not in the list

Do not add these, even though they save prompts. Each lets a mistaken or prompt-injected command act without you seeing it:

- `Bash(ssh *)` or `Bash(scp *)`: would auto-approve writes to production.
- `Bash(security find-generic-password *)`, `Bash(security find-internet-password *)`: reads secrets out of your Keychain.
- `Bash(env)`, `Bash(curl *)`, `Bash(python3 *)`, `Bash(zsh -c *)`, `Bash(sh -c *)`: arbitrary execution or exfiltration.
- `Read(//Users/<you>/**)` or `Read(~/**)`: your whole home folder, including SSH keys and credentials.
- `Bash(gh pr create*)`, `Bash(git push*)`, `Bash(git commit*)`: outward-facing. Approve these each time.
- Any rule containing a token or password. If a command needs `SONAR_TOKEN=...`, an API token or similar, keep it in your Keychain or environment: rule text is stored in plain text.

Check your own settings for the last case (a "No such file" error means that file was not scanned): `grep -nE 'squ_|ghp_|password|_TOKEN=|API_TOKEN|SECRET' ~/.claude/settings*.json .claude/settings*.json`.
