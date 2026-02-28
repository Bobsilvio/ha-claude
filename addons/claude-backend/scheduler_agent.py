"""SchedulerAgent — agente conversazionale per la gestione dei task pianificati.

Usa Claude (Anthropic) con tool_use nativo per un'interfaccia chat-friendly:
  l'utente può scrivere in linguaggio naturale e l'agente crea, elenca,
  elimina e abilita/disabilita task pianificati.

Sessioni con memoria: ogni session_id mantiene la propria cronologia.

Endpoint dedicato in api.py: POST /api/agent/scheduler
"""

import json
import logging
import os
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

# ── Language-aware response instruction ────────────────────────────────────────
# Mirrors the respond_instruction pattern used in api.py LANGUAGE_TEXT

_RESPOND_INSTRUCTION: dict = {
    "en": "Respond in English.",
    "it": "Rispondi sempre in Italiano.",
    "es": "Responde siempre en Español.",
    "fr": "Réponds toujours en Français.",
}

_CRON_TABLE = """\
| Schedule             | Cron              |
|----------------------|-------------------|
| Every day at 8am     | `0 8 * * *`       |
| Mon–Fri at 9:00      | `0 9 * * 1-5`     |
| Every hour           | `0 * * * *`       |
| Every 30 minutes     | `*/30 * * * *`    |
| Midnight             | `0 0 * * *`       |
| Friday at 6pm        | `0 18 * * 5`      |"""

_SYSTEM_PROMPT_TEMPLATE = """\
You are SchedulerAgent 🗓️, the assistant for managing scheduled tasks in the Home Assistant system.

Scheduled tasks automatically send a **message** to the main AI agent on a cron schedule.
The message is processed exactly as if the user had typed it: weather summaries, device reports, reminders, etc.

## What you can do
- **Create** a task: you need a name, a schedule (cron or natural language) and a message
- **List** all tasks with status, next run and run count
- **Delete** a task (built-in system tasks cannot be deleted)
- **Enable / disable** an existing task

## Cron syntax (5 fields: minute hour day month weekday)
{cron_table}

When the user describes a time in natural language, convert it to cron without asking for confirmation.
When creating a task always call the `create_task` tool, then show a brief summary.
**cron** and **message** are always in English in the tool parameters — never translate them.
{respond_instruction}
"""


def _get_system_prompt() -> str:
    """Returns the system prompt localised to the configured LANGUAGE."""
    lang = os.getenv("LANGUAGE", "en").lower()
    respond = _RESPOND_INSTRUCTION.get(lang, _RESPOND_INSTRUCTION["en"])
    return _SYSTEM_PROMPT_TEMPLATE.format(
        cron_table=_CRON_TABLE,
        respond_instruction=respond,
    )

# ── Tool definitions (Anthropic messages API format) ──────────────────────────
# Always in English — these are instructions to Claude, not shown to the user.

_TOOLS = [
    {
        "name": "create_task",
        "description": (
            "Create and save a new scheduled task. "
            "Call this when the user wants to create a schedule."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Task name (e.g. 'Morning briefing')",
                },
                "cron": {
                    "type": "string",
                    "description": "5-field cron expression, e.g. '0 9 * * 1-5'",
                },
                "message": {
                    "type": "string",
                    "description": "Message to send to the main AI agent when the task fires",
                },
                "description": {
                    "type": "string",
                    "description": "Optional human-readable description of the task",
                },
                "enabled": {
                    "type": "boolean",
                    "description": "Whether to activate the task immediately (default: true)",
                },
            },
            "required": ["name", "cron", "message"],
        },
    },
    {
        "name": "list_tasks",
        "description": "Return the list of all scheduled tasks with their current status.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "delete_task",
        "description": (
            "Delete a scheduled task. "
            "Built-in system tasks (e.g. memory_trim) cannot be deleted."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "Task ID to delete (visible in list_tasks output)",
                },
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "toggle_task",
        "description": "Enable or disable a scheduled task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"},
                "enabled": {
                    "type": "boolean",
                    "description": "True = enable, False = disable",
                },
            },
            "required": ["task_id", "enabled"],
        },
    },
]

# ── In-memory session storage ──────────────────────────────────────────────────
# session_id -> list of message dicts (anthropic messages format)
_sessions: dict = {}


def clear_session(session_id: str) -> None:
    """Cancella la cronologia di una sessione."""
    _sessions.pop(session_id, None)


def get_session_history(session_id: str) -> list:
    """Restituisce la cronologia messaggi di una sessione (copia)."""
    return list(_sessions.get(session_id, []))


def list_sessions() -> list:
    """Restituisce tutti i session_id attivi."""
    return list(_sessions.keys())


# ── Tool implementations ───────────────────────────────────────────────────────

def _exec_tool(name: str, inputs: dict) -> str:
    """Esegue un tool e restituisce il risultato come stringa JSON."""
    try:
        import scheduled_tasks as st
        scheduler = st.get_scheduler()
    except Exception as e:
        return json.dumps({"error": f"Scheduler non disponibile: {e}"}, ensure_ascii=False)

    if name == "list_tasks":
        tasks = [
            {
                "task_id": t.task_id,
                "name": t.name,
                "cron": t.cron_expression,
                "description": t.description,
                "enabled": t.enabled,
                "run_count": t.run_count,
                "last_run": t.last_run,
                "next_run": t.next_run,
                "builtin": getattr(t, "builtin", False),
                "message": getattr(t, "message", ""),
            }
            for t in scheduler.tasks.values()
        ]
        return json.dumps({"tasks": tasks, "count": len(tasks)}, ensure_ascii=False)

    if name == "create_task":
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        try:
            task = scheduler.add_message_task(
                task_id=task_id,
                name=inputs["name"],
                cron_expression=inputs["cron"],
                message=inputs["message"],
                description=inputs.get("description", ""),
                enabled=inputs.get("enabled", True),
            )
            return json.dumps(
                {
                    "ok": True,
                    "task_id": task.task_id,
                    "name": task.name,
                    "cron": task.cron_expression,
                    "next_run": task.next_run,
                },
                ensure_ascii=False,
            )
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    if name == "delete_task":
        task_id = inputs.get("task_id", "")
        t = scheduler.tasks.get(task_id)
        if not t:
            return json.dumps({"error": f"Task '{task_id}' non trovato"}, ensure_ascii=False)
        if getattr(t, "builtin", False):
            return json.dumps(
                {"error": f"Il task '{task_id}' è di sistema e non può essere eliminato"},
                ensure_ascii=False,
            )
        ok = scheduler.remove_task(task_id)
        return json.dumps({"ok": ok, "task_id": task_id}, ensure_ascii=False)

    if name == "toggle_task":
        task_id = inputs.get("task_id", "")
        if task_id not in scheduler.tasks:
            return json.dumps({"error": f"Task '{task_id}' non trovato"}, ensure_ascii=False)
        scheduler.tasks[task_id].enabled = inputs["enabled"]
        scheduler.save_tasks()
        return json.dumps(
            {"ok": True, "task_id": task_id, "enabled": inputs["enabled"]},
            ensure_ascii=False,
        )

    return json.dumps({"error": f"Tool '{name}' sconosciuto"}, ensure_ascii=False)


# ── LLM helpers ────────────────────────────────────────────────────────────────

def _get_anthropic_client():
    """
    Restituisce (client, model) con il client Anthropic.
    Lancia RuntimeError se il pacchetto o la chiave non sono disponibili.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY non configurata — SchedulerAgent richiede Anthropic Claude."
        )
    try:
        import anthropic as _ant
    except ImportError:
        raise RuntimeError(
            "Pacchetto 'anthropic' non installato (pip install anthropic)."
        )
    # Usa un modello leggero/veloce; sovra-scrivibile via env
    model = os.getenv("SCHEDULER_AGENT_MODEL", "claude-3-5-haiku-20241022")
    return _ant.Anthropic(api_key=api_key), model


def _content_to_dicts(content) -> list:
    """
    Converte i ContentBlock Anthropic SDK (oggetti Pydantic) in dizionari plain,
    pronti per essere serializzati e rimandati nelle messages successive.
    """
    result = []
    for block in content:
        if hasattr(block, "type"):
            if block.type == "text":
                result.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                result.append(
                    {
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    }
                )
        elif isinstance(block, dict):
            result.append(block)
    return result


# ── Public chat interface ──────────────────────────────────────────────────────

def chat(user_message: str, session_id: str = "default") -> str:
    """
    Processa un messaggio utente e restituisce la risposta dell'agente.

    Args:
        user_message: testo dell'utente
        session_id:   identificativo sessione (mantiene la cronologia)

    Returns:
        Risposta testuale dell'agente (stringa).
    """
    try:
        client, model = _get_anthropic_client()
    except RuntimeError as e:
        return str(e)

    # Costruisce la lista messaggi di questa sessione
    messages = list(_sessions.get(session_id, []))
    messages.append({"role": "user", "content": user_message})

    # Agentic loop — max 6 round-trip per evitare loop infiniti
    for iteration in range(6):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=1024,
                system=_get_system_prompt(),
                tools=_TOOLS,
                messages=messages,
            )
        except Exception as e:
            logger.error(f"SchedulerAgent LLM call failed (iteration {iteration}): {e}")
            return f"Errore chiamata LLM: {e}"

        content_dicts = _content_to_dicts(response.content)

        if response.stop_reason == "end_turn":
            # Risposta testuale finale
            text = " ".join(
                b["text"] for b in content_dicts if b.get("type") == "text"
            ).strip()
            messages.append({"role": "assistant", "content": content_dicts})
            _sessions[session_id] = messages
            return text or "(nessuna risposta)"

        if response.stop_reason == "tool_use":
            # Esegui i tool richiesti e continua il loop
            messages.append({"role": "assistant", "content": content_dicts})
            tool_results = []
            for block in content_dicts:
                if block.get("type") == "tool_use":
                    result_str = _exec_tool(block["name"], block.get("input", {}))
                    logger.debug(
                        f"SchedulerAgent tool '{block['name']}' -> {result_str[:120]}"
                    )
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block["id"],
                            "content": result_str,
                        }
                    )
            messages.append({"role": "user", "content": tool_results})
            continue  # torna al prossimo LLM call

        # stop_reason inatteso (es. "max_tokens")
        logger.warning(f"SchedulerAgent: unexpected stop_reason '{response.stop_reason}'")
        break

    _sessions[session_id] = messages
    return "Limite di iterazioni raggiunto — riprova con una richiesta più semplice."
