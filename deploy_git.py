"""
deploy_git.py
=============
Trevolk Forecasting Engine — Git Deployment Helper

Runs the complete git workflow using Python subprocess so it fully
bypasses the oh-my-posh PowerShell profile alias conflict.

Usage:
    python deploy_git.py
"""

import subprocess
import sys
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ROOT = Path(r"C:\Users\MY PC\OneDrive\Desktop\Trevolk_Forecasting_Engine")
REMOTE = "https://github.com/musa8868973-web/trevolk-forecast-engine"
COMMIT_MSG = "Automated deployment: Git installed and backend modularized"
USER_NAME  = "Muhammad Musa"
USER_EMAIL = "admin@trevolk.com"

# Git executable — winget installs to this path by default
GIT_CANDIDATES = [
    r"C:\Program Files\Git\cmd\git.exe",
    r"C:\Program Files\Git\bin\git.exe",
    r"C:\Users\MY PC\AppData\Local\Programs\Git\cmd\git.exe",
]

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


# ---------------------------------------------------------------------------
# Resolve git.exe
# ---------------------------------------------------------------------------
def find_git() -> str:
    for path in GIT_CANDIDATES:
        if os.path.exists(path):
            return path
    # Fallback: shutil.which (works if PATH was refreshed)
    import shutil
    found = shutil.which("git")
    if found:
        return found
    return None


# ---------------------------------------------------------------------------
# Run helper
# ---------------------------------------------------------------------------
def run(git: str, args: list, check: bool = True, silent_ok_codes=(0,)) -> subprocess.CompletedProcess:
    cmd = [git] + args
    print(f"{CYAN}  > {' '.join(cmd)}{RESET}")
    result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if result.stdout.strip():
        print(f"    {result.stdout.strip()}")
    if result.stderr.strip():
        print(f"    {YELLOW}{result.stderr.strip()}{RESET}")
    if check and result.returncode not in silent_ok_codes:
        print(f"{RED}[FAIL] Exit code {result.returncode}{RESET}")
        sys.exit(result.returncode)
    return result


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def main():
    print(f"\n{BOLD}{CYAN}{'='*60}")
    print("  Trevolk — Git Deployment Pipeline")
    print(f"{'='*60}{RESET}\n")

    # ── Find Git ─────────────────────────────────────────────────────────────
    git = find_git()
    if not git:
        print(f"{RED}[ERROR] git.exe not found. Is Git installed?{RESET}")
        print("  Run: winget install --id Git.Git -e --silent")
        sys.exit(1)

    version = subprocess.run([git, "version"], capture_output=True, text=True)
    print(f"{GREEN}[OK] Git found: {git}{RESET}")
    print(f"     {version.stdout.strip()}\n")

    # ── Step 1: Configure identity ────────────────────────────────────────────
    print(f"{BOLD}[Step 1] Configuring Git identity ...{RESET}")
    run(git, ["config", "--global", "user.name",  USER_NAME])
    run(git, ["config", "--global", "user.email", USER_EMAIL])
    print(f"{GREEN}  Identity set: {USER_NAME} <{USER_EMAIL}>{RESET}\n")

    # ── Step 2: git init ──────────────────────────────────────────────────────
    print(f"{BOLD}[Step 2] Initialising repository ...{RESET}")
    git_dir = ROOT / ".git"
    if git_dir.exists():
        print(f"  {YELLOW}Repo already initialised — skipping git init.{RESET}")
    else:
        run(git, ["-C", str(ROOT), "init"])
    print()

    # ── Step 3: Set branch to main ────────────────────────────────────────────
    print(f"{BOLD}[Step 3] Setting branch to 'main' ...{RESET}")
    run(git, ["-C", str(ROOT), "branch", "-M", "main"], silent_ok_codes=(0, 1))
    print()

    # ── Step 4: Add remote ────────────────────────────────────────────────────
    print(f"{BOLD}[Step 4] Configuring remote origin ...{RESET}")
    check_remote = subprocess.run(
        [git, "-C", str(ROOT), "remote", "get-url", "origin"],
        capture_output=True, text=True
    )
    if check_remote.returncode == 0:
        current = check_remote.stdout.strip()
        print(f"  {YELLOW}Remote already exists: {current}{RESET}")
        if current != REMOTE:
            print(f"  Updating remote to: {REMOTE}")
            run(git, ["-C", str(ROOT), "remote", "set-url", "origin", REMOTE])
    else:
        run(git, ["-C", str(ROOT), "remote", "add", "origin", REMOTE])
        print(f"  {GREEN}Remote added: {REMOTE}{RESET}")
    print()

    # ── Step 5: Stage all files ───────────────────────────────────────────────
    print(f"{BOLD}[Step 5] Staging files (respecting .gitignore) ...{RESET}")
    run(git, ["-C", str(ROOT), "add", "."])

    staged = subprocess.run(
        [git, "-C", str(ROOT), "diff", "--cached", "--name-only"],
        capture_output=True, text=True
    )
    files = staged.stdout.strip().splitlines()
    if files:
        print(f"  {len(files)} file(s) staged:")
        for f in files:
            print(f"    + {f}")

        # Safety check — make sure .env and .pkl are NOT staged
        dangerous = [f for f in files if f.endswith(('.env', '.pkl', '.joblib'))]
        if dangerous:
            print(f"\n{RED}[SECURITY HALT] These sensitive files are staged:{RESET}")
            for d in dangerous:
                print(f"    !! {d}")
            print(f"{RED}Check your .gitignore and run 'git rm --cached <file>' first.{RESET}")
            sys.exit(1)
    else:
        print(f"  {YELLOW}Nothing new to stage — working tree is clean.{RESET}")
    print()

    # ── Step 6: Commit ────────────────────────────────────────────────────────
    print(f"{BOLD}[Step 6] Committing ...{RESET}")
    commit_result = subprocess.run(
        [git, "-C", str(ROOT), "commit", "-m", COMMIT_MSG],
        capture_output=True, text=True
    )
    print(f"    {commit_result.stdout.strip()}")
    if commit_result.stderr.strip():
        print(f"    {YELLOW}{commit_result.stderr.strip()}{RESET}")
    print()

    # ── Step 7: Push ─────────────────────────────────────────────────────────
    print(f"{BOLD}[Step 7] Pushing to GitHub ...{RESET}")
    print(f"  {CYAN}NOTE: If prompted, use your GitHub Personal Access Token as the password.{RESET}")
    print(f"  Generate one at: GitHub → Settings → Developer Settings → PAT → Fine-grained\n")

    push_result = subprocess.run(
        [git, "-C", str(ROOT), "push", "-u", "origin", "main"],
        capture_output=True, text=True
    )
    print(f"    {push_result.stdout.strip()}")
    if push_result.stderr.strip():
        print(f"    {push_result.stderr.strip()}")

    if push_result.returncode == 0:
        print(f"\n{GREEN}{BOLD}{'='*60}")
        print("  SUCCESS! Code is live on GitHub.")
        print(f"  {REMOTE}{RESET}")
        print(f"{GREEN}{'='*60}{RESET}\n")
    else:
        print(f"\n{RED}[FAIL] Push failed (exit code {push_result.returncode}).{RESET}")
        print("  Common fixes:")
        print("  1. Authentication: use a PAT, not your GitHub password.")
        print("  2. Repo doesn't exist: create it at github.com first (no README).")
        print("  3. Branch conflict: run  git pull --rebase origin main  then retry.")
        sys.exit(push_result.returncode)


if __name__ == "__main__":
    main()
