#!/usr/bin/env python3
"""
Scheduled Tasks Module (Cron-like Automation)

Features:
- Cron expression parsing (minute, hour, day, month, weekday)
- Background task execution
- Task history tracking
- Error handling and retry logic
- Task enable/disable
"""

import os
import json
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, List, Any
from enum import Enum
from dataclasses import dataclass, asdict, field
import logging

logger = logging.getLogger(__name__)

TASKS_FILE = "/config/amira/scheduled_tasks.json"


class CronExpression:
    """Simple cron expression parser (minute hour day month weekday)."""
    
    MONTH_MAP = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
    }
    
    # Python uses 0=Monday, 6=Sunday
    # Cron uses 0 or 7=Sunday, 1-6=Monday-Saturday
    # We convert to Python's weekday() format (0-6 where 0=Monday)
    WEEKDAY_MAP = {
        "sun": 6,   # Sunday = 6 in Python
        "mon": 0,   # Monday = 0 in Python
        "tue": 1,
        "wed": 2,
        "thu": 3,
        "fri": 4,
        "sat": 5
    }
    
    def __init__(self, expression: str):
        """Parse cron expression: minute hour day month weekday."""
        parts = expression.split()
        if len(parts) != 5:
            raise ValueError(f"Cron expression must have 5 parts, got {len(parts)}")
        
        self.minute = self._parse_field(parts[0], 0, 59, "minute")
        self.hour = self._parse_field(parts[1], 0, 23, "hour")
        self.day = self._parse_field(parts[2], 1, 31, "day")
        self.month = self._parse_field(parts[3], 1, 12, "month", self.MONTH_MAP)
        self.weekday = self._parse_field(parts[4], 0, 6, "weekday", self.WEEKDAY_MAP)
    
    @staticmethod
    def _parse_field(field: str, min_val: int, max_val: int, name: str = "", aliases: Optional[Dict] = None) -> set:
        """Parse a single cron field."""
        if field == "*":
            return set(range(min_val, max_val + 1))
        
        values = set()
        for part in field.split(","):
            part = part.strip()
            
            # Handle aliases (jan, mon, etc.)
            if aliases and part.lower() in aliases:
                values.add(aliases[part.lower()])
            # Handle ranges (1-5)
            elif "-" in part:
                start, end = part.split("-")
                if aliases and start.lower() in aliases:
                    start = aliases[start.lower()]
                if aliases and end.lower() in aliases:
                    end = aliases[end.lower()]
                start_val = int(start)
                end_val = int(end)
                
                # Special case for weekday: convert cron (0-7) to Python (0-6)
                if name == "weekday":
                    if start_val == 0:
                        start_val = 6  # Sunday
                    elif start_val == 7:
                        start_val = 6  # Sunday (alternate notation)
                    else:
                        start_val = start_val - 1  # Mon=1->0, Tue=2->1, etc.
                    
                    if end_val == 0:
                        end_val = 6
                    elif end_val == 7:
                        end_val = 6
                    else:
                        end_val = end_val - 1
                
                values.update(range(start_val, end_val + 1))
            # Handle step values (*/5, 0-30/5)
            elif "/" in part:
                range_part, step = part.split("/")
                step = int(step)
                if range_part == "*":
                    values.update(range(min_val, max_val + 1, step))
                else:
                    start, end = range_part.split("-")
                    start_val = int(start)
                    end_val = int(end)
                    values.update(range(start_val, end_val + 1, step))
            # Single value
            else:
                val = int(part)
                # Special case for weekday: convert cron (0-7) to Python (0-6)
                if name == "weekday":
                    if val == 0 or val == 7:
                        val = 6  # Sunday
                    else:
                        val = val - 1  # 1->0, 2->1, etc.
                values.add(val)
        
        return values
    
    def matches(self, dt: datetime) -> bool:
        """Check if datetime matches this cron expression."""
        return (
            dt.minute in self.minute and
            dt.hour in self.hour and
            dt.day in self.day and
            dt.month in self.month and
            dt.weekday() in self.weekday
        )


@dataclass
class TaskExecution:
    """Single task execution record."""
    task_id: str
    executed_at: str
    duration_seconds: float
    success: bool
    error: Optional[str] = None
    result: Optional[str] = None


@dataclass
class ScheduledTask:
    """Scheduled task definition."""
    task_id: str
    name: str
    cron_expression: str
    description: str = ""
    enabled: bool = True
    created_at: str = ""
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0
    error_count: int = 0
    message: str = ""      # If set, this text is sent to the agent when the task fires
    builtin: bool = False  # Built-in tasks cannot be deleted via API

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class TaskScheduler:
    """Main task scheduler."""
    
    def __init__(self, check_interval_seconds: int = 60,
                 message_callback: Optional[Callable[[str, str], None]] = None):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.task_callbacks: Dict[str, Callable] = {}
        self.execution_history: Dict[str, List[TaskExecution]] = {}
        self.check_interval = check_interval_seconds
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.last_run_check: Dict[str, datetime] = {}
        # Optional callback for message-based tasks: fn(task_id, message)
        self.message_callback: Optional[Callable[[str, str], None]] = message_callback
    
    def register_task(
        self,
        task_id: str,
        name: str,
        cron_expression: str,
        callback: Callable,
        description: str = "",
        enabled: bool = True,
        builtin: bool = False,
    ) -> None:
        """Register a new scheduled task with a Python callback."""
        # Validate cron expression
        try:
            CronExpression(cron_expression)
        except ValueError as e:
            raise ValueError(f"Invalid cron expression: {e}")
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            cron_expression=cron_expression,
            description=description,
            enabled=enabled,
            builtin=builtin,
        )
        
        self.tasks[task_id] = task
        self.task_callbacks[task_id] = callback
        self.execution_history[task_id] = []
        
        logger.info(f"Task registered: {task_id} - {name} ({cron_expression})")

    def add_message_task(
        self,
        task_id: str,
        name: str,
        cron_expression: str,
        message: str,
        description: str = "",
        enabled: bool = True,
    ) -> ScheduledTask:
        """Add a task that fires a message to the agent (nanobot-style).
        
        The message is passed to the message_callback (if set) when the task fires.
        These tasks are persisted to disk and survive restarts.
        """
        try:
            CronExpression(cron_expression)
        except ValueError as e:
            raise ValueError(f"Invalid cron expression: {e}")

        task = ScheduledTask(
            task_id=task_id,
            name=name,
            cron_expression=cron_expression,
            description=description,
            enabled=enabled,
            message=message,
        )
        self.tasks[task_id] = task
        self.execution_history[task_id] = []
        self.save_tasks()
        logger.info(f"Message task added: {task_id} - {name} [{cron_expression}]")
        return task

    def remove_task(self, task_id: str) -> bool:
        """Remove a task. Built-in tasks cannot be removed."""
        task = self.tasks.get(task_id)
        if not task:
            return False
        if task.builtin:
            logger.warning(f"Cannot remove built-in task: {task_id}")
            return False
        del self.tasks[task_id]
        self.task_callbacks.pop(task_id, None)
        self.execution_history.pop(task_id, None)
        self.save_tasks()
        logger.info(f"Task removed: {task_id}")
        return True

    def save_tasks(self) -> None:
        """Persist message-based tasks to disk."""
        try:
            os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
            data = []
            for t in self.tasks.values():
                if t.message and not t.builtin:  # only persist message-based, non-builtin tasks
                    data.append({
                        "task_id": t.task_id,
                        "name": t.name,
                        "cron_expression": t.cron_expression,
                        "description": t.description,
                        "enabled": t.enabled,
                        "message": t.message,
                        "created_at": t.created_at,
                        "run_count": t.run_count,
                        "error_count": t.error_count,
                    })
            with open(TASKS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Could not save tasks: {e}")

    def load_tasks(self) -> int:
        """Load persisted message-based tasks from disk. Returns count loaded."""
        if not os.path.exists(TASKS_FILE):
            return 0
        try:
            with open(TASKS_FILE, encoding="utf-8") as f:
                data = json.load(f)
            loaded = 0
            for item in data:
                task_id = item.get("task_id", "")
                if task_id and task_id not in self.tasks:
                    t = ScheduledTask(
                        task_id=task_id,
                        name=item.get("name", task_id),
                        cron_expression=item.get("cron_expression", ""),
                        description=item.get("description", ""),
                        enabled=item.get("enabled", True),
                        message=item.get("message", ""),
                        created_at=item.get("created_at", ""),
                        run_count=item.get("run_count", 0),
                        error_count=item.get("error_count", 0),
                    )
                    self.tasks[task_id] = t
                    self.execution_history[task_id] = []
                    loaded += 1
            if loaded:
                logger.info(f"Loaded {loaded} scheduled tasks from disk")
            return loaded
        except Exception as e:
            logger.warning(f"Could not load tasks: {e}")
            return 0
    
    def unregister_task(self, task_id: str) -> None:
        """Unregister a task (alias for remove_task, kept for backward compat)."""
        self.remove_task(task_id)
    
    def enable_task(self, task_id: str) -> None:
        """Enable a task."""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            logger.info(f"Task enabled: {task_id}")
    
    def disable_task(self, task_id: str) -> None:
        """Disable a task."""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            logger.info(f"Task disabled: {task_id}")
    
    def _execute_task(self, task_id: str) -> None:
        """Execute a single task."""
        task = self.tasks[task_id]
        callback = self.task_callbacks.get(task_id)
        
        start_time = time.time()
        execution = TaskExecution(
            task_id=task_id,
            executed_at=datetime.now().isoformat(),
            duration_seconds=0,
            success=False
        )
        
        try:
            logger.info(f"Executing task: {task_id} - {task.name}")
            result = None
            if callback:
                result = callback()
            elif task.message and self.message_callback:
                # nanobot-style: fire the message to the agent
                self.message_callback(task_id, task.message)
                result = f"Message sent: {task.message[:60]}"
            else:
                result = "no-op (no callback or message)"
            
            execution.success = True
            execution.result = str(result)[:200] if result else None
            task.run_count += 1
            task.last_run = execution.executed_at
            
            logger.info(f"Task completed: {task_id}")
        except Exception as e:
            execution.success = False
            execution.error = str(e)
            task.error_count += 1
            task.last_run = execution.executed_at
            
            logger.error(f"Task failed: {task_id} - {e}")
        
        finally:
            execution.duration_seconds = time.time() - start_time
            self.execution_history[task_id].append(execution)
            
            # Keep last 100 executions
            if len(self.execution_history[task_id]) > 100:
                self.execution_history[task_id].pop(0)
            
            # Persist updated run_count/last_run for message tasks
            if task.message and not task.builtin:
                self.save_tasks()
    
    def _calculate_next_run(self, task: ScheduledTask) -> Optional[datetime]:
        """Calculate next run time for a task."""
        try:
            cron = CronExpression(task.cron_expression)
            now = datetime.now()
            
            # Check next hour
            for _ in range(24 * 60):  # Check up to 24 hours
                test_time = now + timedelta(minutes=1)
                if cron.matches(test_time):
                    return test_time
                now = test_time
            
            return None
        except:
            return None
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop (runs in background thread)."""
        logger.info("Scheduler started")
        
        while self.running:
            try:
                now = datetime.now()
                
                for task_id, task in self.tasks.items():
                    if not task.enabled:
                        continue
                    
                    # Check if should run
                    try:
                        cron = CronExpression(task.cron_expression)
                        
                        # Prevent running same task twice per minute
                        last_run = self.last_run_check.get(task_id)
                        if last_run and (now - last_run).seconds < 60:
                            continue
                        
                        if cron.matches(now):
                            self.last_run_check[task_id] = now
                            self._execute_task(task_id)
                            
                            # Calculate next run
                            task.next_run = self._calculate_next_run(task).isoformat() if self._calculate_next_run(task) else None
                    except Exception as e:
                        logger.error(f"Scheduler error for {task_id}: {e}")
                
                # Sleep until next minute
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                time.sleep(self.check_interval)
        
        logger.info("Scheduler stopped")
    
    def start(self) -> None:
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("Scheduler thread started")
    
    def stop(self) -> None:
        """Stop the scheduler."""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Scheduler stopped")
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get task details."""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[ScheduledTask]:
        """Get all tasks."""
        return list(self.tasks.values())
    
    def get_task_history(self, task_id: str, limit: int = 10) -> List[TaskExecution]:
        """Get execution history for a task."""
        history = self.execution_history.get(task_id, [])
        return history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        total_runs = sum(t.run_count for t in self.tasks.values())
        total_errors = sum(t.error_count for t in self.tasks.values())
        success_rate = (total_runs - total_errors) / total_runs * 100 if total_runs > 0 else 0
        
        return {
            "running": self.running,
            "total_tasks": len(self.tasks),
            "enabled_tasks": sum(1 for t in self.tasks.values() if t.enabled),
            "total_runs": total_runs,
            "total_errors": total_errors,
            "success_rate": f"{success_rate:.1f}%",
            "tasks": [
                {
                    "id": t.task_id,
                    "name": t.name,
                    "cron": t.cron_expression,
                    "enabled": t.enabled,
                    "runs": t.run_count,
                    "errors": t.error_count,
                    "last_run": t.last_run,
                    "next_run": t.next_run,
                }
                for t in self.tasks.values()
            ]
        }


# Global scheduler instance
_scheduler: Optional[TaskScheduler] = None


def initialize_scheduler(check_interval: int = 60,
                         message_callback=None) -> TaskScheduler:
    """Initialize global scheduler."""
    global _scheduler
    _scheduler = TaskScheduler(check_interval_seconds=check_interval,
                               message_callback=message_callback)
    # Load persisted message tasks from disk
    _scheduler.load_tasks()
    _scheduler.start()
    logger.info("Task scheduler initialized")
    return _scheduler


def get_scheduler() -> Optional[TaskScheduler]:
    """Get global scheduler instance."""
    if _scheduler is None:
        initialize_scheduler()
    return _scheduler


def shutdown_scheduler() -> None:
    """Shutdown global scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.stop()
        _scheduler = None
        logger.info("Task scheduler shutdown")


if __name__ == "__main__":
    # Quick demo
    logging.basicConfig(level=logging.INFO)
    
    scheduler = TaskScheduler()
    
    # Register some demo tasks
    def demo_task_1():
        return "Task 1 executed"
    
    def demo_task_2():
        return "Task 2 executed"
    
    scheduler.register_task(
        "demo_hourly",
        "Demo Hourly Task",
        "0 * * * *",  # Every hour at minute 0
        demo_task_1,
        "Runs every hour"
    )
    
    scheduler.register_task(
        "demo_daily",
        "Demo Daily Task",
        "0 9 * * *",  # Every day at 9:00
        demo_task_2,
        "Runs daily at 9am"
    )
    
    print("Scheduler stats:", json.dumps(scheduler.get_stats(), indent=2))
