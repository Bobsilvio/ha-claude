"""Session and daily cost/usage tracking with disk persistence.

Inspired by OpenClaw's session-cost-usage.ts — tracks tokens, cost
breakdowns, and daily aggregates.  Data is saved to /data/usage_stats.json.

Thread-safe: uses a lock so the SSE stream can record usage from
concurrent requests without races.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Disk location (Home Assistant add-on persistent storage)
# ---------------------------------------------------------------------------
_USAGE_FILE = os.environ.get("USAGE_STATS_FILE", "/data/usage_stats.json")

# ---------------------------------------------------------------------------
# Types (mirrors OpenClaw CostUsageTotals / CostUsageDailyEntry)
# ---------------------------------------------------------------------------

def _empty_totals() -> Dict[str, Any]:
    """Return a zeroed-out totals dict."""
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "total_tokens": 0,
        "total_cost": 0.0,
        "input_cost": 0.0,
        "output_cost": 0.0,
        "cache_read_cost": 0.0,
        "cache_write_cost": 0.0,
        "requests": 0,
    }


def _add_totals(dst: Dict[str, Any], src: Dict[str, Any]) -> None:
    """Accumulate *src* into *dst* in-place."""
    for key in (
        "input_tokens", "output_tokens", "cache_read_tokens",
        "cache_write_tokens", "total_tokens", "requests",
    ):
        dst[key] = dst.get(key, 0) + src.get(key, 0)
    for key in (
        "total_cost", "input_cost", "output_cost",
        "cache_read_cost", "cache_write_cost",
    ):
        dst[key] = round(dst.get(key, 0.0) + src.get(key, 0.0), 6)


# ---------------------------------------------------------------------------
# UsageTracker singleton
# ---------------------------------------------------------------------------

class UsageTracker:
    """Accumulates usage per day, per model, per provider. Persists to disk."""

    def __init__(self, path: str = _USAGE_FILE) -> None:
        self._path = path
        self._lock = threading.Lock()
        # In-memory state ─ loaded from disk on first access
        self._data: Optional[Dict[str, Any]] = None

    # -- lazy load ----------------------------------------------------------

    def _ensure_loaded(self) -> Dict[str, Any]:
        if self._data is None:
            self._data = self._load()
        return self._data

    def _load(self) -> Dict[str, Any]:
        """Load stats from disk, returning empty structure on error."""
        try:
            if os.path.exists(self._path):
                with open(self._path, "r") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "daily" in data:
                    return data
        except Exception as e:
            logger.warning("usage_tracker: could not load %s: %s", self._path, e)
        return {"daily": {}, "totals": _empty_totals(), "by_model": {}, "by_provider": {}}

    def _save(self) -> None:
        """Persist current state to disk (called under lock)."""
        if self._data is None:
            return
        try:
            os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
            tmp = self._path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(self._data, f, indent=2, default=str)
            os.replace(tmp, self._path)
        except Exception as e:
            logger.warning("usage_tracker: could not save %s: %s", self._path, e)

    # -- public API ---------------------------------------------------------

    def record(self, usage: Dict[str, Any]) -> None:
        """Record a single request's usage.

        *usage* should contain the enriched dict from api.py stream processing:
            input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,
            cost, cost_breakdown, currency, model, provider
        """
        with self._lock:
            data = self._ensure_loaded()
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

            # Build entry from usage dict
            entry = _empty_totals()
            entry["input_tokens"] = usage.get("input_tokens", 0)
            entry["output_tokens"] = usage.get("output_tokens", 0)
            entry["cache_read_tokens"] = usage.get("cache_read_tokens", 0)
            entry["cache_write_tokens"] = usage.get("cache_write_tokens", 0)
            entry["total_tokens"] = (
                entry["input_tokens"] + entry["output_tokens"]
                + entry["cache_read_tokens"] + entry["cache_write_tokens"]
            )
            entry["total_cost"] = usage.get("cost", 0.0)
            bd = usage.get("cost_breakdown") or {}
            entry["input_cost"] = bd.get("input", 0.0)
            entry["output_cost"] = bd.get("output", 0.0)
            entry["cache_read_cost"] = bd.get("cache_read", 0.0)
            entry["cache_write_cost"] = bd.get("cache_write", 0.0)
            entry["requests"] = 1

            # -- daily --
            if today not in data["daily"]:
                data["daily"][today] = _empty_totals()
            _add_totals(data["daily"][today], entry)

            # -- global totals --
            _add_totals(data["totals"], entry)

            # -- by model --
            model = usage.get("model") or "unknown"
            if model not in data.setdefault("by_model", {}):
                data["by_model"][model] = _empty_totals()
            _add_totals(data["by_model"][model], entry)

            # -- by provider --
            provider = usage.get("provider") or "unknown"
            if provider not in data.setdefault("by_provider", {}):
                data["by_provider"][provider] = _empty_totals()
            _add_totals(data["by_provider"][provider], entry)

            self._save()

    def get_summary(self, days: int = 30) -> Dict[str, Any]:
        """Return a summary of usage for the last N days.

        Response shape (mirrors OpenClaw CostUsageSummary):
            {
                updated_at: ISO string,
                days: int,
                totals: CostUsageTotals,
                daily: [{date, ...totals}],
                by_model: {model: totals},
                by_provider: {provider: totals},
            }
        """
        with self._lock:
            data = self._ensure_loaded()

        # Filter daily entries to requested window
        all_dates = sorted(data.get("daily", {}).keys(), reverse=True)
        recent_dates = all_dates[:days]

        daily_list: List[Dict[str, Any]] = []
        window_totals = _empty_totals()
        for d in sorted(recent_dates):
            day_data = data["daily"][d]
            daily_list.append({"date": d, **day_data})
            _add_totals(window_totals, day_data)

        return {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "days": days,
            "totals": window_totals,
            "all_time_totals": data.get("totals", _empty_totals()),
            "daily": daily_list,
            "by_model": data.get("by_model", {}),
            "by_provider": data.get("by_provider", {}),
        }

    def get_today(self) -> Dict[str, Any]:
        """Quick access to today's totals."""
        with self._lock:
            data = self._ensure_loaded()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return data.get("daily", {}).get(today, _empty_totals())

    def reset(self) -> None:
        """Clear all tracked data."""
        with self._lock:
            self._data = {"daily": {}, "totals": _empty_totals(), "by_model": {}, "by_provider": {}}
            self._save()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_tracker: Optional[UsageTracker] = None


def get_tracker() -> UsageTracker:
    """Get or create the global UsageTracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = UsageTracker()
    return _tracker
