"""
ship_it.py
==========
Trevolk Forecasting Engine — Master DevSecOps Automation Script

Pipeline (in strict order):
  Step A  →  Security scans  (bandit  +  safety)
  Step B  →  Generate PDF documentation
  Step C  →  Git workflow  (init → branch → remote → add → commit → push)
  Step D  →  Start local Uvicorn server

Usage (from the project root in VS Code terminal):
    python ship_it.py

Optional flags:
    python ship_it.py --skip-git     Skip the Git workflow (useful for local-only runs)
    python ship_it.py --skip-server  Don't start the server after push
    python ship_it.py --skip-scans   Bypass security scans (NOT recommended)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.resolve()
APP_DIR = PROJECT_ROOT / "app"
REMOTE_URL = "https://github.com/musa8868973-web/trevolk-forecast-engine"
COMMIT_MSG = (
    "Automated DevSecOps pipeline: PDF generated, security checked, "
    "and backend modularized"
)
BANDIT_REPORT = PROJECT_ROOT / "bandit_report.json"
SAFETY_REPORT = PROJECT_ROOT / "safety_report.json"

# ANSI colours (Windows 10+ supports these in PowerShell / CMD)
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def banner(text: str) -> None:
    width = 68
    print(f"\n{CYAN}{BOLD}{'=' * width}")
    print(f"  {text}")
    print(f"{'=' * width}{RESET}")


def info(msg: str) -> None:
    print(f"{GREEN}[INFO]{RESET}  {msg}")


def warn(msg: str) -> None:
    print(f"{YELLOW}[WARN]{RESET}  {msg}")


def error(msg: str) -> None:
    print(f"{RED}[ERROR]{RESET} {msg}", file=sys.stderr)


def run(
    cmd: list[str],
    *,
    capture: bool = False,
    check: bool = True,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess:
    """Run a subprocess command with clear stdout/stderr passthrough."""
    info(f"Running: {' '.join(cmd)}")
    return subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        check=check,
        cwd=str(cwd or PROJECT_ROOT),
    )


def abort(reason: str) -> None:
    error(reason)
    error("Pipeline halted. Fix the issues above before re-running ship_it.py.")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Dependency pre-flight
# ---------------------------------------------------------------------------
def check_tool(name: str) -> None:
    """Ensure an external CLI tool is on PATH."""
    result = subprocess.run(
        ["where" if sys.platform == "win32" else "which", name],
        capture_output=True,
    )
    if result.returncode != 0:
        abort(
            f"'{name}' is not installed or not on PATH.\n"
            f"  Fix: pip install {name}"
        )


# ---------------------------------------------------------------------------
# Step A: Security Scans
# ---------------------------------------------------------------------------
def step_a_security_scans(args: argparse.Namespace) -> None:
    banner("STEP A — Security Scanning")

    if args.skip_scans:
        warn("--skip-scans flag detected. Skipping security scans. (NOT recommended)")
        return

    # --- Pre-flight ---
    for tool in ("bandit", "safety"):
        check_tool(tool)

    # ── Bandit (AST-based static analysis) ──────────────────────────────────
    info("Running Bandit on app/ directory …")
    bandit_result = subprocess.run(
        [
            "bandit",
            "--recursive",
            "--format", "json",
            "--output", str(BANDIT_REPORT),
            "--severity-level", "medium",   # flag MEDIUM+ severity only
            "--confidence-level", "medium",  # flag MEDIUM+ confidence only
            str(APP_DIR),
        ],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )

    # Bandit exits 0 (no issues), 1 (issues found), or 2 (error)
    if bandit_result.returncode == 2:
        abort(f"Bandit encountered an error:\n{bandit_result.stderr}")

    if bandit_result.returncode == 1:
        error(
            f"Bandit found security issues in app/.\n"
            f"  Report saved to: {BANDIT_REPORT}\n"
            f"  Review and fix all MEDIUM+ severity issues before proceeding."
        )
        # Print a quick human-readable summary
        summary_result = subprocess.run(
            ["bandit", "--recursive", "--severity-level", "medium",
             "--confidence-level", "medium", str(APP_DIR)],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        print(summary_result.stdout[-3000:])  # last 3000 chars to avoid flood
        abort("Bandit scan FAILED. Pipeline halted.")
    else:
        info(f"Bandit scan PASSED. No medium/high severity issues found.")
        info(f"  Full JSON report: {BANDIT_REPORT}")

    # ── Safety (dependency vulnerability check) ──────────────────────────────
    info("Running Safety on installed packages …")
    safety_result = subprocess.run(
        ["safety", "check", "--json", "--output", str(SAFETY_REPORT)],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )

    if safety_result.returncode != 0:
        error(
            f"Safety found vulnerable dependencies!\n"
            f"  Report saved to: {SAFETY_REPORT}\n"
            f"  Run 'safety check' manually to see details and update requirements.txt."
        )
        print(safety_result.stdout[-2000:])
        abort("Safety scan FAILED. Pipeline halted.")
    else:
        info("Safety scan PASSED. No known vulnerabilities found.")
        info(f"  Full JSON report: {SAFETY_REPORT}")


# ---------------------------------------------------------------------------
# Step B: Generate PDF Documentation
# ---------------------------------------------------------------------------
def step_b_generate_docs() -> None:
    banner("STEP B — Generating PDF Architecture Documentation")

    pdf_script = PROJECT_ROOT / "generate_pdf_docs.py"
    if not pdf_script.exists():
        abort(f"generate_pdf_docs.py not found at {pdf_script}")

    try:
        run([sys.executable, str(pdf_script)])
    except subprocess.CalledProcessError as exc:
        abort(f"PDF generation failed (exit code {exc.returncode}). "
              "Ensure 'reportlab' is installed: pip install reportlab")

    pdf_output = PROJECT_ROOT / "Trevolk_API_Architecture.pdf"
    if pdf_output.exists():
        info(f"PDF created successfully: {pdf_output}")
    else:
        warn("PDF script ran but output file was not found — check generate_pdf_docs.py.")


# ---------------------------------------------------------------------------
# Step C: Git Workflow
# ---------------------------------------------------------------------------
def step_c_git_workflow(args: argparse.Namespace) -> None:
    banner("STEP C — Git Workflow")

    if args.skip_git:
        warn("--skip-git flag detected. Skipping entire Git workflow.")
        return

    check_tool("git")

    # ── git init (safe — no-op if already a repo) ───────────────────────────
    git_dir = PROJECT_ROOT / ".git"
    if not git_dir.exists():
        info("Initialising new Git repository …")
        run(["git", "init"])
    else:
        info("Git repository already initialised.")

    # ── Set branch to main ───────────────────────────────────────────────────
    run(["git", "branch", "-M", "main"], check=False)

    # ── Add remote (ignore error if already exists) ──────────────────────────
    remote_check = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    if remote_check.returncode != 0:
        info(f"Adding remote origin: {REMOTE_URL}")
        run(["git", "remote", "add", "origin", REMOTE_URL])
    else:
        info(f"Remote 'origin' already set to: {remote_check.stdout.strip()}")

    # ── Stage all files ───────────────────────────────────────────────────────
    info("Staging all files (respecting .gitignore) …")
    run(["git", "add", "."])

    # Show what's staged so the user can verify nothing sensitive slipped in
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    if staged.stdout.strip():
        info("Files staged for commit:")
        for f in staged.stdout.strip().splitlines():
            print(f"    + {f}")
    else:
        warn("Nothing new to commit — working tree is clean. Skipping commit & push.")
        return

    # ── Commit ────────────────────────────────────────────────────────────────
    info(f'Committing with message: "{COMMIT_MSG}"')
    try:
        run(["git", "commit", "-m", COMMIT_MSG])
    except subprocess.CalledProcessError:
        warn("git commit returned a non-zero exit code — possibly nothing to commit.")

    # ── Push ─────────────────────────────────────────────────────────────────
    info("Pushing to origin/main …")
    try:
        run(["git", "push", "-u", "origin", "main"])
        info("Push successful!")
    except subprocess.CalledProcessError as exc:
        abort(
            f"git push failed (exit code {exc.returncode}).\n"
            "  Common causes:\n"
            "    1. You are not authenticated — run: git credential-manager configure\n"
            "    2. The remote repo does not exist yet — create it on GitHub first.\n"
            "    3. The remote has diverged — run: git pull --rebase origin main"
        )


# ---------------------------------------------------------------------------
# Step D: Start Local Server
# ---------------------------------------------------------------------------
def step_d_start_server(args: argparse.Namespace) -> None:
    banner("STEP D — Starting Uvicorn Development Server")

    if args.skip_server:
        warn("--skip-server flag detected. Skipping server start.")
        return

    print(f"""
{CYAN}{BOLD}  Trevolk Forecasting Engine is starting …
  ──────────────────────────────────────────────────
  Local API:     http://localhost:8000
  Swagger UI:    http://localhost:8000/docs
  ReDoc:         http://localhost:8000/redoc
  Health check:  http://localhost:8000/health
  ──────────────────────────────────────────────────
  Press CTRL+C to stop the server.{RESET}
""")

    # This call is BLOCKING — it keeps the script alive while uvicorn runs.
    try:
        run(
            [
                sys.executable, "-m", "uvicorn",
                "app.main:app",
                "--reload",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--log-level", "info",
            ],
            check=False,   # Don't abort if user hits CTRL+C (exit code 1)
        )
    except KeyboardInterrupt:
        info("Server stopped by user.")


# ---------------------------------------------------------------------------
# Argument Parser
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Trevolk Forecasting Engine — DevSecOps Automation Pipeline",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--skip-scans",
        action="store_true",
        help="Bypass bandit and safety scans. NOT recommended.",
    )
    parser.add_argument(
        "--skip-git",
        action="store_true",
        help="Skip the entire Git workflow (init, commit, push).",
    )
    parser.add_argument(
        "--skip-server",
        action="store_true",
        help="Do not start the Uvicorn server after the pipeline completes.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------
def main() -> None:
    args = parse_args()

    print(f"""
{CYAN}{BOLD}
╔══════════════════════════════════════════════════════════════════╗
║         Trevolk Forecasting Engine — DevSecOps Pipeline          ║
║                      ship_it.py  v2.0.0                          ║
╚══════════════════════════════════════════════════════════════════╝{RESET}
""")

    step_a_security_scans(args)
    step_b_generate_docs()
    step_c_git_workflow(args)
    step_d_start_server(args)

    banner("Pipeline Complete")
    info("All steps finished successfully.")


if __name__ == "__main__":
    main()
