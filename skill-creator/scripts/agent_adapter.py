#!/usr/bin/env python3
"""Agent-runtime adapter: decouples skill-creator from any specific agent.

The tooling needs exactly two capabilities from the host agent runtime:

1. run_query() -- run one headless agent session on a query, with a
   candidate skill registered, and report whether the skill was used.
2. call_llm()  -- send a text prompt to a language model, get text back.

Any non-interactive agent CLI can be plugged in via environment variables
(or an agent_config.json file -- see references/agent_config.md):

  SKILL_AGENT_QUERY_CMD        Shell template for one headless query.
                               Placeholders: {query} (shell-escaped; if
                               omitted the query goes to stdin), {model},
                               {skill_file}, {skill_dir}.
  SKILL_AGENT_LLM_CMD          Shell template for one LLM completion.
                               Prompt goes to stdin unless {prompt} appears.
                               Placeholders: {prompt}, {model}.
  SKILL_AGENT_MODEL            Default model id for {model}.
  SKILL_AGENT_SKILLS_DIR       Where the candidate skill is registered for
                               trigger tests (your agent's skill discovery
                               directory). Default: .agent/skills.
  SKILL_AGENT_TRIGGER_REGEX    Regex on the agent's output deciding whether
                               the skill triggered. {token} is replaced with
                               the run's unique token. Default matches the
                               self-report marker injected into the
                               registered skill copy.
  SKILL_AGENT_PROJECT_ROOT     Working directory for test queries (default: cwd).
  SKILL_AGENT_TIMEOUT          Default timeout per command, in seconds.
  SKILL_AGENT_ENV_UNSET        Comma-separated env vars stripped from child
                               processes (some CLIs block nested sessions).
  SKILL_AGENT_PRESET           Optional defaults: generic | codex | claude-code.
  SKILL_AGENT_CONFIG           Path to a JSON config file with the same keys
                               in snake_case (default: ./agent_config.json).

Precedence: environment variables > config file > preset > built-in defaults.
"""

from __future__ import annotations

import json
import os
import re
import select
import shlex
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

ENV_PREFIX = "SKILL_AGENT_"

CONFIG_KEYS = (
    "query_cmd", "llm_cmd", "model", "skills_dir", "trigger_regex",
    "project_root", "timeout", "env_unset", "preset",
)

# Optional starting points only -- nothing here is hard-wired to a framework.
PRESETS: dict[str, dict] = {
    "generic": {},
    "codex": {
        "query_cmd": "codex exec {query}",
        "llm_cmd": "codex exec {prompt}",
        "skills_dir": ".codex/prompts",
    },
    "claude-code": {
        "query_cmd": "claude -p {query}",
        "llm_cmd": "claude -p",
        "skills_dir": ".claude/commands",
        "env_unset": ["CLAUDECODE"],
    },
}

DEFAULT_SKILLS_DIR = ".agent/skills"
DEFAULT_TRIGGER_REGEX = r"\[SKILL-USED:{token}\]"
DEFAULT_TIMEOUT = 300

_MARKER = (
    "\n\n> **Trigger-test self-report protocol (injected by the skill-creator"
    " test harness):** If and only if this skill is being used to handle the"
    " current task, include the exact token `[SKILL-USED:{token}]` in your"
    " final reply.\n"
)


def _load_config() -> dict:
    config: dict = {}
    config_path = os.environ.get(ENV_PREFIX + "CONFIG")
    candidate = Path(config_path) if config_path else Path("agent_config.json")
    if candidate.is_file():
        config.update(json.loads(candidate.read_text()))
    preset_name = os.environ.get(ENV_PREFIX + "PRESET") or config.get("preset") or ""
    if preset_name:
        if preset_name not in PRESETS:
            raise ValueError(
                f"Unknown {ENV_PREFIX}PRESET {preset_name!r}; known: {sorted(PRESETS)}"
            )
        merged = dict(PRESETS[preset_name])
        merged.update(config)
        config = merged
    for key in CONFIG_KEYS:
        value = os.environ.get(ENV_PREFIX + key.upper())
        if value:
            config[key] = value.split(",") if key == "env_unset" else value
    return config


@dataclass
class RegisteredSkill:
    token: str
    path: Path


class AgentAdapter:
    """Thin wrapper around a configured agent CLI. See module docstring."""

    def __init__(self, config: dict | None = None):
        self.config = _load_config() if config is None else config
        c = self.config
        self.query_cmd = c.get("query_cmd") or None
        self.llm_cmd = c.get("llm_cmd") or None
        self.model = c.get("model") or None
        self.skills_dir = c.get("skills_dir") or DEFAULT_SKILLS_DIR
        self.trigger_regex = c.get("trigger_regex") or DEFAULT_TRIGGER_REGEX
        self.project_root = Path(c.get("project_root") or Path.cwd())
        self.timeout = int(c.get("timeout") or DEFAULT_TIMEOUT)
        self.env_unset = list(c.get("env_unset") or [])

    def _child_env(self) -> dict:
        return {k: v for k, v in os.environ.items() if k not in self.env_unset}

    def _build_command(self, template: str, text: str, model: str | None) -> tuple[list[str], str | None]:
        """Render a command template into (argv, stdin_text).

        The text is embedded shell-escaped when the template contains
        {prompt} or {query}; otherwise it is passed on stdin.
        """
        resolved_model = model or self.model or ""
        if "{model}" in template and not resolved_model:
            raise RuntimeError(
                f"{ENV_PREFIX}MODEL (or --model) is required by command template {template!r}"
            )
        rendered = template.replace("{model}", shlex.quote(resolved_model) if resolved_model else "")
        stdin_text = None
        for placeholder in ("{prompt}", "{query}"):
            if placeholder in template:
                rendered = rendered.replace(placeholder, shlex.quote(text))
                break
        else:
            stdin_text = text
        return shlex.split(rendered), stdin_text

    # --- capability 1: one headless query with a candidate skill ----------

    def register_skill(self, skill_name: str, description: str) -> RegisteredSkill:
        """Write the candidate skill (with self-report marker) into skills_dir."""
        token = f"{skill_name}-skill-{uuid.uuid4().hex[:8]}"
        skills_dir = Path(self.skills_dir)
        if not skills_dir.is_absolute():
            skills_dir = self.project_root / skills_dir
        skills_dir.mkdir(parents=True, exist_ok=True)
        path = skills_dir / f"{token}.md"
        indented = "\n  ".join(description.split("\n"))
        path.write_text(
            f"---\nname: {token}\ndescription: |\n  {indented}\n---\n\n"
            f"# {skill_name}\n\nThis skill handles: {description}\n"
            + _MARKER.replace("{token}", token)
        )
        return RegisteredSkill(token=token, path=path)

    def unregister_skill(self, reg: RegisteredSkill) -> None:
        try:
            reg.path.unlink()
        except OSError:
            pass

    def run_query(self, query: str, reg: RegisteredSkill, timeout: int | None = None,
                  model: str | None = None) -> tuple[bool, str]:
        """Run one headless agent query; return (triggered, captured_output)."""
        if not self.query_cmd:
            raise RuntimeError(
                "No agent query command configured. Set SKILL_AGENT_QUERY_CMD or "
                "SKILL_AGENT_PRESET (see references/agent_config.md)."
            )
        timeout = timeout or self.timeout
        template = (self.query_cmd
                    .replace("{skill_file}", shlex.quote(str(reg.path)))
                    .replace("{skill_dir}", shlex.quote(str(reg.path.parent))))
        cmd, stdin_text = self._build_command(template, query, model)
        pattern = re.compile(self.trigger_regex.replace("{token}", re.escape(reg.token)))

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE if stdin_text is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=str(self.project_root),
            env=self._child_env(),
        )
        if stdin_text is not None:
            process.stdin.write(stdin_text.encode("utf-8"))
            process.stdin.close()

        parts: list[str] = []
        triggered = False
        deadline = time.time() + timeout
        try:
            while time.time() < deadline:
                ready, _, _ = select.select([process.stdout], [], [], 1.0)
                if not ready:
                    continue
                chunk = os.read(process.stdout.fileno(), 8192)
                if not chunk:
                    break
                parts.append(chunk.decode("utf-8", errors="replace"))
                if pattern.search("".join(parts)):
                    triggered = True
                    break
        finally:
            if process.poll() is None:
                process.kill()
            process.wait()
            remaining = process.stdout.read()
            if remaining:
                parts.append(remaining.decode("utf-8", errors="replace"))

        output = "".join(parts)
        return triggered or bool(pattern.search(output)), output

    # --- capability 2: one LLM text completion ---------------------------

    def call_llm(self, prompt: str, model: str | None = None, timeout: int | None = None) -> str:
        """Send the prompt to the configured LLM command; return its stdout."""
        if not self.llm_cmd:
            raise RuntimeError(
                "No LLM command configured. Set SKILL_AGENT_LLM_CMD or "
                "SKILL_AGENT_PRESET (see references/agent_config.md)."
            )
        cmd, stdin_text = self._build_command(self.llm_cmd, prompt, model)
        result = subprocess.run(
            cmd,
            input=stdin_text if stdin_text is not None else "",
            capture_output=True,
            text=True,
            env=self._child_env(),
            cwd=str(self.project_root),
            timeout=timeout or self.timeout,
        )
        if result.returncode != 0:
            raise RuntimeError(f"{self.llm_cmd!r} exited {result.returncode}\nstderr: {result.stderr}")
        return result.stdout