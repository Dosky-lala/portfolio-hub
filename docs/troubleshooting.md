# Troubleshooting log: Chapter 1 (Portfolio Hub)

Every real problem hit while building this project: what broke, how it was diagnosed, the root cause, the fix, and the lesson.
Errors are content: each entry is a debugging story worth more than the fix itself.

Environment: Windows + WSL2 (Ubuntu), native Docker Engine, GitHub Actions. Slow, high-latency network (relevant to several entries).

## Index

| # | Problem | Area |
|---|---|---|
| 1 | Commits under the wrong identity, pushes with the wrong key | Git / SSH |
| 2 | Windows `npm` leaking into WSL; a silently failed install | WSL / tooling |
| 3 | "DNS failure" that was really extreme latency | Networking |
| 4 | `command not found: from` | Shell |
| 5 | Three different files, identical sizes | Files |
| 6 | Stray `backend/backend/` directory committed | Git |
| 7 | `Errno 98`: port 8000 already in use | Processes |
| 8 | `pkill` matched a container; `kill` said "Operation not permitted" | Containers |
| 9 | Vulnerability gate failed on an upstream base image | Security / CI |
| 10 | Linter findings that depended on the linter's version | Linting |
| 11 | An undo command reverted the wrong work | Git |
| 12 | `502 Bad Gateway` right after a rebuild | Containers / Nginx |
| 13 | ESLint error: setState inside an effect | Frontend |
| 14 | A Dependabot merge introduced Node version drift | Dependencies |
| 15 | Python 3.15 slipped in as a "minor" update | Dependencies |
| 16 | A docs-only PR failed the security gate | Security / CI |
| 17 | Tangled branches and stale CI results | Git / CI |
| 18 | Five green checks, merge still blocked | GitHub rulesets |

---

## 1. Commits under the wrong identity, pushes with the wrong key

- **Symptom:** commits were attributed to the wrong account, and pushes authenticated with a key belonging to a different GitHub user.
- **Diagnosis:** `git config user.email` and `ssh -T git@github.com` showed which identity and key were actually in use.
- **Root cause:** a global Git identity and default SSH key left over from other work.
- **Fix:** a dedicated key (`~/.ssh/id_ed25519_github`) with `IdentitiesOnly yes` in `~/.ssh/config`, and the GitHub **noreply** email so a personal address never appears in public history.
- **Lesson:** verify *who* Git thinks you are before the first commit. Identity mistakes live forever in history.

## 2. Windows `npm` leaking into WSL; a silently failed install

- **Symptom:** `npm` ran, but from `/mnt/c/...`, with unrelated Windows global packages attached. Node from `nvm` wasn't actually installed.
- **Diagnosis:** `which -a npm` showed a Windows path ahead of the Linux one.
- **Root cause:** WSL appends the Windows `PATH` by default, and the `nvm` installer had failed without stopping the script.
- **Fix:** reinstalled `nvm` with a fail-loud download (`curl -f`), then confirmed `which node` points inside `~/.nvm`.
- **Lesson:** in WSL, always check *which* binary runs. Scripts should fail loudly, never continue silently.

## 3. "DNS failure" that was really extreme latency

- **Symptom:** `curl: (6) Could not resolve host`, intermittently.
- **Diagnosis:** `/etc/resolv.conf` (WSL's `10.255.255.254`) was correct, but `ping` showed latencies near **10,000 ms**. Lookups were timing out, not failing.
- **Root cause:** network latency, surfacing as a DNS error.
- **Fix:** `curl --connect-timeout 30 --retry 3`. Recurred later as `no such host` during a Docker base-image pull; mitigated by retrying, or deferring verification to CI's faster network.
- **Lesson:** **the error message isn't the diagnosis.** Measure before you fix.

## 4. `command not found: from`

- **Symptom:** bash complained about `from`, `import` and other Python keywords.
- **Root cause:** Python code pasted into the shell instead of into a file.
- **Fix:** write code to files (editor or heredoc), and run it with `python`.
- **Lesson:** know which interpreter is reading your input.

## 5. Three different files, identical sizes

- **Symptom:** three source files that should differ were all exactly 974 bytes.
- **Diagnosis:** `ls -la` showed identical sizes; `md5sum` showed identical hashes. (The well-known empty-file MD5 is `d41d8cd9...`, useful for spotting empty files.)
- **Root cause:** the same content pasted into all three files.
- **Fix:** rewrote each file, verified with `md5sum`.
- **Lesson:** sizes and hashes are cheap sanity checks. Use them after bulk file creation.

## 6. Stray `backend/backend/` directory committed

- **Symptom:** an empty `backend/backend/app/main.py` appeared in the repo.
- **Root cause:** a command run from the wrong directory created a nested path, and it was committed.
- **Fix:** `git rm -r backend/backend` in a new commit. No history rewrite needed for an empty file.
- **Lesson:** harmless files can be removed going forward, but **a committed secret is different: rotate it first**, because it remains in history.

## 7. `Errno 98`: port 8000 already in use

- **Symptom:** uvicorn couldn't start because the address was in use.
- **Diagnosis:** `ss -tlnp | grep 8000` and `pgrep -af uvicorn` found an orphaned server in a forgotten VS Code terminal.
- **Fix:** `pkill` (SIGTERM, which lets the process clean up) rather than `kill -9` (SIGKILL, which doesn't).
- **Lesson:** find the process before killing it, and escalate signals gradually.

## 8. `pkill` matched a container; `kill` said "Operation not permitted"

- **Symptom:** `pkill -f uvicorn` also matched the *containerized* uvicorn, and `kill` on it was refused.
- **Root cause:** **containers are ordinary host processes** with isolation applied. The container ran as UID 10001, which the host user had no permission to signal.
- **Fix:** manage containers through Docker: `docker compose stop`.
- **Lesson:** a non-root container really is a different user, even from the host's point of view. (Bonus check: `ss -tlnp` confirmed only `127.0.0.1:8080` was exposed, proving the network design.)

## 9. Vulnerability gate failed on an upstream base image

- **Symptom:** after hardening, the backend passed the Trivy gate but the frontend failed: 3 fixable HIGH CVEs (brotli, curl, libcurl).
- **Diagnosis:** `docker compose build --pull` resolved the **same** base-image digest. Upstream hadn't published a rebuilt image yet.
- **Root cause:** inherited vulnerabilities, fixed in Alpine but not yet in the upstream image.
- **Fix:** a targeted `apk upgrade` of only those packages, switching to root for one step and straight back to the unprivileged user. Follow-up: Hadolint DL3066 flagged `USER root`, fixed with the numeric `USER 0`.
- **Lesson:** you inherit vulnerabilities on *someone else's* schedule. Also: an "info"-level lint finding still fails CI, so check exit codes, not just eyeballs.

## 10. Linter findings that depended on the linter's version

- **Symptom:** Ruff reported B008 (`Depends()` in argument defaults) and RUF100 (unused `noqa`), which didn't appear under earlier assumptions.
- **Root cause:** relying on Ruff's **default** rule set, which changes between versions.
- **Fix:** an explicit `ruff.toml` pinning the rule set; refactored to FastAPI's recommended `Annotated` dependencies (fixing B008 properly rather than silencing it); added exception chaining (`raise ... from err`, B904). The 13-test suite verified the refactor changed no behavior.
- **Lesson:** pin tool configuration, not just tool versions. When a linter points at a better pattern, adopt the pattern.

## 11. An undo command reverted the wrong work

- **Symptom:** a commit added `ruff.toml` but not the refactored code it required. The repo's own lint check would fail.
- **Diagnosis:** `git status` showed no `M` (modified) where one was expected.
- **Root cause:** `git checkout -- app/main.py`, used to undo a deliberate test bug, restored the **last committed** version, wiping the uncommitted refactor along with the bug.
- **Fix:** re-applied the refactor, verified with tests and lint, committed separately.
- **Lesson:** an undo command reverts to a *specific state*. Know which one. Commit before experimenting.

## 12. `502 Bad Gateway` right after a rebuild

- **Symptom:** Nginx returned 502 immediately after rebuilding the backend.
- **Hypotheses:** (A) a startup race; (B) Nginx caching the old container IP from its startup-time DNS lookup.
- **Diagnosis:** retrying 10 seconds later returned 200, confirming (A). (B) is a real latent risk in Compose, recorded but not fixed, since Kubernetes Services provide stable IPs.
- **Fix:** `docker compose up --wait`, which blocks until healthchecks pass.
- **Lesson:** **"started" isn't "ready."** Gather evidence before applying the more complex fix.

## 13. ESLint error: setState inside an effect

- **Symptom:** `react-hooks/set-state-in-effect` *error* (not warning). Caught by running lint locally before the first CI run.
- **Root cause:** data loading called state setters from the effect body, which also hid a race: overlapping fetches could overwrite fresh data with stale data.
- **Fix:** fetch inside the effect, set state only in `.then()` callbacks guarded by an `ignore` cleanup flag, with a single `version` counter driving all reloads.
- **Lesson:** run the pipeline's checks locally first, so CI confirms rather than discovers.

## 14. A Dependabot merge introduced Node version drift

- **Symptom:** after "merging the pytest update," pytest was still at the old version.
- **Diagnosis:** `git log` showed the merged PR was actually **Node 24 -> 26** for the frontend build image, a major version.
- **Root cause:** a PR merged without reading its title and diff. It left laptop and CI on Node 24 while Docker built with Node 26.
- **Fix:** confirmed Node 26 was LTS (`nvm ls-remote --lts`), then aligned everything via a single `.nvmrc`, read by both nvm and CI. Told Dependabot to skip Node majors (odd-numbered majors never become LTS).
- **Lesson:** read a PR's title and diff before merging. Runtime upgrades are decisions, not routine updates.

## 15. Python 3.15 slipped in as a "minor" update

- **Symptom:** a Dependabot PR moved the backend image to Python 3.15 while laptop and CI stayed on 3.14.
- **Root cause:** Dependabot treats 3.14 -> 3.15 as a semver *minor* update, so the major-only ignore rule didn't apply. Python's "minor" releases are feature releases.
- **Fix:** pinned 3.14 via `backend/.python-version` (read by CI), refreshed the 3.14 digest, and set Dependabot to ignore Python minor and major base-image bumps.
- **Lesson:** version numbers don't always mean what semantic versioning implies. One source of truth per runtime.

## 16. A docs-only PR failed the security gate

- **Symptom:** a pull request changing only documentation and test names failed `Build & scan (frontend)`. The next day, the backend failed too.
- **Diagnosis:** Trivy found newly published fixable HIGH CVEs: frontend expat (x4), musl, zlib; backend apt, zlib1g. The images hadn't changed; the vulnerability database had.
- **Root cause:** **digest pinning freezes your packages, not your risk.** A pinned image becomes less safe over time.
- **Fix:** replaced the growing targeted patch list with a **policy**: apply all available OS security updates at build time (`apk upgrade` / `apt-get upgrade`), safe because both images track stable branches that ship only bug and security fixes. Every build is still scanned.
- **Lesson:** CVE publication is a continuous stream. A pipeline needs a policy for it, not a series of one-off patches. (Side note: one CVE carried a mislabeled description; trust the package and fixed version over the prose.)

## 17. Tangled branches and stale CI results

- **Symptom:** after the fix, CI still showed the old CVE versions, then contradictory green and red results.
- **Diagnosis:** `git status` showed the backend fix **uncommitted**; `git log` showed a postmortem commit made directly on local `main` had leaked into the fix branch. Later, a red result belonged to a run from before a force push; one "refresh" commit landed on the wrong branch.
- **Fix:** committed the fix; `git rebase --onto origin/main <stray-commit>` to move only the fix commits; `git push --force-with-lease`; `git reset --hard origin/main` on local `main` (after confirming the stray work existed on its own branch). Found the authoritative run by commit: `gh run list --commit <sha>`.
- **Side lessons from the GitHub CLI:** piped `gh` commands can't prompt, so pass IDs explicitly; read IDs from `--json`, never from truncated tables; `<placeholder>` brackets are shell redirection, so remove them.
- **Lesson:** `git branch --show-current`, `git status` and `git log --oneline -3` before every commit and push. Identify CI runs **by commit**, not by "the latest thing I see."

## 18. Five green checks, merge still blocked

- **Symptom:** every check passed, yet the merge was refused: "base branch policy prohibits the merge."
- **Diagnosis:** ruled out required approvals (set to 0). `gh api repos/.../rules/branches/main` showed the raw configuration: **one** required check whose name was the entire comma-separated list of five names.
- **Root cause:** all names typed into a single entry when the ruleset was created. No workflow could ever report a check with that name.
- **Fix:** five separate entries, each selected from the suggestions (which come from real runs, so they match exactly). Separately, `gh pr merge` failed with "Resource not accessible by personal access token"; merged in the browser, with `gh auth refresh -s repo` as the CLI fix.
- **Lesson:** when a system says a requirement isn't met against visibly green evidence, **read the requirement's raw configuration. The API shows what's configured; the UI shows what you think you configured.**

---

## Patterns across all 18

1. **Evidence before fixes.** Several "obvious" diagnoses (#3, #12, #14) were wrong until measured.
2. **Know exactly what state you're in:** which binary, which branch, which commit, which run, which identity (#1, #2, #11, #17).
3. **Pin everything, then keep it moving.** Pins prevent surprises; Dependabot, update policies and scanning prevent rot (#9, #14, #15, #16).
4. **Configuration is code.** Pin linter rules, read rulesets via the API, keep runtime versions in one file (#10, #15, #18).
5. **Run CI's checks locally first,** so the pipeline confirms instead of discovering (#13).
