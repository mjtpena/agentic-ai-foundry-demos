"""
Tiny zero-dependency console-styling + env helpers shared by every demo.

Keeping this here means each demo file stays focused on the *Foundry* concept it
teaches (prompt agent, MCP tool, A2A, retrieval, guardrails) instead of
re-implementing argument parsing and pretty-printing. Nothing here is required
by the slides — it's the "amazing beyond" polish layer.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

# --- .env loading -----------------------------------------------------------
def load_env() -> None:
    """Load the repo-root .env (written by infra/provision.sh) if present.

    Uses python-dotenv when available, else a minimal parser so the demos still
    run in a bare environment.
    """
    root = Path(__file__).resolve().parents[1]
    env_path = root / ".env"
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path, override=False)
        load_dotenv(root / ".env.local", override=True)  # personal overrides
    except ImportError:  # pragma: no cover - fallback
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def env(name: str, *fallbacks: str, default: str | None = None, required: bool = False) -> str | None:
    """Return the first non-empty env var among name+fallbacks."""
    for key in (name, *fallbacks):
        val = os.environ.get(key)
        if val:
            return val
    if required:
        rule(f"Missing required environment variable: {name}", style="error")
        print(
            f"  Set it in .env (run infra/provision.sh) or export {name}=...",
            file=sys.stderr,
        )
        sys.exit(2)
    return default


# --- ANSI styling (degrades gracefully when not a TTY) ----------------------
_TTY = sys.stdout.isatty()
def _c(code: str) -> str:
    return code if _TTY else ""

RESET = _c("\033[0m"); BOLD = _c("\033[1m"); DIM = _c("\033[2m")
BLUE = _c("\033[34m"); GREEN = _c("\033[32m"); YELLOW = _c("\033[33m")
RED = _c("\033[31m"); CYAN = _c("\033[36m"); MAGENTA = _c("\033[35m")

_STYLES = {
    "info": (BLUE, "==>"), "ok": (GREEN, " ✓ "), "warn": (YELLOW, " ! "),
    "error": (RED, " ✗ "), "step": (CYAN, "▶"), "agent": (MAGENTA, "🤖"),
}

def rule(msg: str, style: str = "info") -> None:
    color, glyph = _STYLES.get(style, (BLUE, "==>"))
    print(f"{color}{BOLD}{glyph}{RESET} {msg}")

def banner(title: str, subtitle: str = "") -> None:
    line = "─" * min(len(title) + 4, 76)
    print(f"\n{CYAN}{line}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    if subtitle:
        print(f"{DIM}  {subtitle}{RESET}")
    print(f"{CYAN}{line}{RESET}")

def user_says(text: str) -> None:
    print(f"\n{BOLD}{GREEN}You ▸{RESET} {text}")

def agent_says(text: str) -> None:
    print(f"{BOLD}{MAGENTA}Agent ▸{RESET} {text}")

class Spinner:
    """Lightweight 'working…' indicator for the gaps while the service thinks."""
    FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    def __init__(self, label: str = "thinking"):
        self.label, self._i, self._on = label, 0, False
    def tick(self) -> None:
        if not _TTY:
            return
        sys.stdout.write(f"\r{DIM}{self.FRAMES[self._i % len(self.FRAMES)]} {self.label}…{RESET}")
        sys.stdout.flush(); self._i += 1; self._on = True
    def clear(self) -> None:
        if self._on and _TTY:
            sys.stdout.write("\r" + " " * (len(self.label) + 12) + "\r"); sys.stdout.flush()
        self._on = False
