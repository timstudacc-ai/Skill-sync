# Configuring the agent runtime

The skill-creator scripts are framework-agnostic. They need two capabilities
from the host environment, each supplied by a shell command template:

| Capability | Used by | Config key |
|---|---|---|
| Run one headless agent query with a candidate skill available | `run_eval.py`, `run_loop.py` | `query_cmd` |
| Get one plain-text LLM completion | `improve_description.py`, `run_loop.py` | `llm_cmd` |

## Configuration

Settings are resolved from (highest precedence first):

1. Environment variables prefixed `SKILL_AGENT_`
2. A JSON config file: `SKILL_AGENT_CONFIG=/path/to/agent_config.json`
   (or `./agent_config.json` if present)
3. A preset selected with `SKILL_AGENT_PRESET`
4. Built-in defaults

| Env var | JSON key | Meaning |
|---|---|---|
| `SKILL_AGENT_QUERY_CMD` | `query_cmd` | Shell template for one headless query. Placeholders: `{query}` (shell-escaped query text; if omitted the query is passed on stdin), `{model}`, `{skill_file}` (path of the registered test skill), `{skill_dir}` |
| `SKILL_AGENT_LLM_CMD` | `llm_cmd` | Shell template for one LLM completion. The prompt is passed on stdin unless `{prompt}` appears in the template. Placeholders: `{prompt}`, `{model}` |
| `SKILL_AGENT_MODEL` | `model` | Default model id substituted for `{model}` (the `--model` CLI flag overrides it) |
| `SKILL_AGENT_SKILLS_DIR` | `skills_dir` | Directory where the candidate skill is registered for trigger tests. Should be your agent's skill/command discovery directory. Default: `.agent/skills` |
| `SKILL_AGENT_TRIGGER_REGEX` | `trigger_regex` | Regex applied to the agent's output; a match counts as "skill triggered". `{token}` is replaced by the run's unique token. Default matches the self-report marker (see below) |
| `SKILL_AGENT_PROJECT_ROOT` | `project_root` | Working directory for test queries. Default: the current directory |
| `SKILL_AGENT_TIMEOUT` | `timeout` | Default timeout per command, in seconds (default 300) |
| `SKILL_AGENT_ENV_UNSET` | `env_unset` | Comma-separated env vars stripped from child processes (some CLIs refuse nested sessions) |
| `SKILL_AGENT_PRESET` | `preset` | Optional preset filling in defaults: `generic` (default), `codex`, `claude-code` |

## How trigger detection works

`run_eval.py` registers a *copy* of the skill under a unique token
(`<name>-skill-<hex>`) in `skills_dir`, with one extra instruction in its
body: when the skill is used, the agent must include `[SKILL-USED:<token>]`
in its reply. After the query runs, the captured output is scanned for that
marker — a match means the skill was consulted. This works with any agent
whose output you can capture; no framework-specific event streams are parsed.

If your agent can't follow the self-report instruction (e.g. it echoes skill
contents verbatim instead of answering), set `trigger_regex` to match
something your agent emits when it reads a skill, such as the skill file path.

## Examples

Generic CLI agent, prompt as an argument:

```bash
export SKILL_AGENT_QUERY_CMD='my-agent exec {query}'
export SKILL_AGENT_LLM_CMD='my-agent exec {prompt}'
export SKILL_AGENT_SKILLS_DIR="$HOME/.my-agent/skills"
```

Wrapper script (full control over how the skill is exposed to the agent):

```bash
export SKILL_AGENT_QUERY_CMD='/home/me/bin/agent-wrapper.sh {query} {skill_file}'
```

Model selection:

```bash
export SKILL_AGENT_MODEL='some-model-id'
# or per invocation:
python -m scripts.run_eval ... --model some-model-id
```

## Requirements

- Python 3.10+ and a non-interactive agent CLI (one that accepts a prompt
  and prints a response).
- Trigger tests additionally need the agent to discover skills from a
  directory (`skills_dir`). If your agent has no such mechanism, description
  optimization won't work; the qualitative review loop still does.