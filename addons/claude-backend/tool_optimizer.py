"""Tool execution optimization and batching.

Inspired by nanobot: Optimize tool execution by:
- Batching multiple parallel calls
- Deduplicating identical calls
- Reordering for efficiency
- Caching results within request
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
import hashlib
import json

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """Represents a single tool call."""
    tool_name: str
    arguments: Dict[str, Any]
    call_id: str = ""
    
    def __post_init__(self):
        """Generate unique ID."""
        if not self.call_id:
            hash_str = hashlib.md5(
                json.dumps([self.tool_name, self.arguments], sort_keys=True).encode()
            ).hexdigest()
            self.call_id = f"{self.tool_name}_{hash_str[:8]}"
    
    def is_same_as(self, other: 'ToolCall') -> bool:
        """Check if two tool calls are identical."""
        return (self.tool_name == other.tool_name and 
                self.arguments == other.arguments)


@dataclass
class ToolResult:
    """Represents the result of a tool call."""
    call_id: str
    tool_name: str
    arguments: Dict[str, Any]
    result: Any
    execution_time_ms: float
    error: Optional[str] = None
    cached: bool = False
    
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.error is None


class ToolExecutionOptimizer:
    """Optimizes and batches tool execution."""
    
    def __init__(self):
        """Initialize optimizer."""
        self.result_cache: Dict[str, ToolResult] = {}  # call_id -> result
        self.execution_log: List[ToolResult] = []
    
    def deduplicate_calls(self, calls: List[ToolCall]) -> Tuple[List[ToolCall], Dict[str, str]]:
        """Remove duplicate calls and create mapping.
        
        Args:
            calls: List of tool calls
            
        Returns:
            Tuple of (deduplicated_calls, mapping_from_original_to_dedup)
        """
        seen: Dict[str, ToolCall] = {}
        mapping: Dict[str, str] = {}
        dedup: List[ToolCall] = []
        
        for call in calls:
            # Create dedup key
            dedup_key = json.dumps([call.tool_name, call.arguments], sort_keys=True)
            
            if dedup_key in seen:
                # Already seen, map to existing
                mapping[call.call_id] = seen[dedup_key].call_id
                logger.debug(f"Dedup: {call.tool_name} (id: {call.call_id[:8]} → {seen[dedup_key].call_id[:8]})")
            else:
                # New call
                seen[dedup_key] = call
                dedup.append(call)
                mapping[call.call_id] = call.call_id
        
        removed = len(calls) - len(dedup)
        if removed > 0:
            logger.info(f"Deduplicated {removed} identical tool calls")
        
        return dedup, mapping
    
    def prioritize_calls(self, calls: List[ToolCall]) -> List[ToolCall]:
        """Prioritize tool calls for better UX.
        
        Priority order:
        1. read_* calls (no side effects, safe)
        2. get_* calls (queries)
        3. check_* calls (validation)
        4. apply_* calls (modifications)
        5. write_* calls (destructive)
        """
        priority_prefixes = {
            "read": 0,
            "get": 1,
            "check": 2,
            "apply": 3,
            "write": 4,
        }
        
        def get_priority(call: ToolCall) -> int:
            for prefix, priority in priority_prefixes.items():
                if call.tool_name.startswith(prefix):
                    return priority
            return 5  # Unknown = lowest priority
        
        sorted_calls = sorted(calls, key=get_priority)
        
        if sorted_calls != calls:
            logger.debug(f"Reordered {len(calls)} tool calls by priority")
        
        return sorted_calls
    
    def batch_calls(self, calls: List[ToolCall], parallel_limit: int = 5) -> List[List[ToolCall]]:
        """Batch calls for parallel execution.
        
        Args:
            calls: List of tool calls
            parallel_limit: Max tools to run in parallel
            
        Returns:
            List of batches (each batch can run in parallel)
        """
        batches: List[List[ToolCall]] = []
        current_batch: List[ToolCall] = []
        
        # Track which entities are being modified (to avoid conflicts)
        modified_entities: set = set()
        
        for call in calls:
            # Extract entity/path from arguments
            entity = None
            if "entity_id" in call.arguments:
                entity = call.arguments["entity_id"]
            elif "file" in call.arguments:
                entity = call.arguments["file"]
            elif "path" in call.arguments:
                entity = call.arguments["path"]
            
            # Check for conflicts
            has_conflict = entity and entity in modified_entities
            
            # Start new batch if limit reached or conflict detected
            if len(current_batch) >= parallel_limit or has_conflict:
                if current_batch:
                    batches.append(current_batch)
                    modified_entities.clear()
                current_batch = []
            
            current_batch.append(call)
            if entity:
                modified_entities.add(entity)
        
        if current_batch:
            batches.append(current_batch)
        
        logger.info(f"Batched {len(calls)} calls into {len(batches)} batches "
                   f"(parallel limit: {parallel_limit})")
        
        return batches
    
    def execute_batch_parallel(self, 
                              batch: List[ToolCall],
                              execute_fn: Callable) -> List[ToolResult]:
        """Execute batch of calls (simulating parallelism where possible).
        
        Args:
            batch: List of tool calls to execute
            execute_fn: Function to execute (takes ToolCall, returns result)
            
        Returns:
            List of ToolResult objects
        """
        results: List[ToolResult] = []
        
        for call in batch:
            start_time = time.time()
            
            try:
                # Check cache first
                if call.call_id in self.result_cache:
                    cached_result = self.result_cache[call.call_id]
                    cached_result.cached = True
                    results.append(cached_result)
                    logger.debug(f"✅ {call.tool_name} (cached, id: {call.call_id[:8]})")
                    continue
                
                # Execute
                result_data = execute_fn(call)
                execution_time = (time.time() - start_time) * 1000
                
                # Create result
                result = ToolResult(
                    call_id=call.call_id,
                    tool_name=call.tool_name,
                    arguments=call.arguments,
                    result=result_data,
                    execution_time_ms=execution_time,
                )
                
                # Cache result
                self.result_cache[call.call_id] = result
                results.append(result)
                
                logger.debug(f"✅ {call.tool_name} ({execution_time:.0f}ms, id: {call.call_id[:8]})")
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                
                result = ToolResult(
                    call_id=call.call_id,
                    tool_name=call.tool_name,
                    arguments=call.arguments,
                    result=None,
                    execution_time_ms=execution_time,
                    error=str(e),
                )
                
                results.append(result)
                logger.error(f"❌ {call.tool_name}: {str(e)[:100]} (id: {call.call_id[:8]})")
        
        self.execution_log.extend(results)
        return results
    
    def optimize_and_execute(self, 
                            calls: List[ToolCall],
                            execute_fn: Callable,
                            parallel_limit: int = 5) -> Dict[str, ToolResult]:
        """Fully optimized execution pipeline.
        
        Args:
            calls: List of tool calls
            execute_fn: Function to execute single call
            parallel_limit: Max parallel executions
            
        Returns:
            Dict mapping call_id to ToolResult
        """
        logger.info(f"Optimizing {len(calls)} tool calls...")
        
        # Step 1: Deduplicate
        dedup_calls, mapping = self.deduplicate_calls(calls)
        
        # Step 2: Prioritize
        prioritized = self.prioritize_calls(dedup_calls)
        
        # Step 3: Batch
        batches = self.batch_calls(prioritized, parallel_limit)
        
        # Step 4: Execute all batches
        results: Dict[str, ToolResult] = {}
        for batch_idx, batch in enumerate(batches):
            logger.debug(f"Executing batch {batch_idx + 1}/{len(batches)} ({len(batch)} calls)")
            batch_results = self.execute_batch_parallel(batch, execute_fn)
            
            for result in batch_results:
                results[result.call_id] = result
        
        # Step 5: Map deduplicated results back to originals
        final_results = {}
        for original_id, dedup_id in mapping.items():
            if dedup_id in results:
                result = results[dedup_id]
                # Preserve original call ID but share result
                final_results[original_id] = result
        
        # Statistics
        total_time = sum(r.execution_time_ms for r in results.values())
        success_count = sum(1 for r in results.values() if r.is_success())
        
        logger.info(f"Optimization complete: {success_count}/{len(results)} success, "
                   f"{total_time:.0f}ms total execution")
        
        return final_results
    
    def stats(self) -> Dict[str, Any]:
        """Get optimization statistics."""
        if not self.execution_log:
            return {"executions": 0}
        
        success = sum(1 for r in self.execution_log if r.is_success())
        cached = sum(1 for r in self.execution_log if r.cached)
        total_time = sum(r.execution_time_ms for r in self.execution_log)
        
        return {
            "total_executions": len(self.execution_log),
            "successful": success,
            "failed": len(self.execution_log) - success,
            "cached": cached,
            "total_execution_time_ms": total_time,
            "avg_execution_time_ms": total_time / len(self.execution_log),
            "cache_utilization": f"{cached / len(self.execution_log) * 100:.1f}%",
        }


# Global optimizer instance
_tool_optimizer: Optional[ToolExecutionOptimizer] = None


def get_tool_optimizer() -> ToolExecutionOptimizer:
    """Get or create global tool optimizer."""
    global _tool_optimizer
    if _tool_optimizer is None:
        _tool_optimizer = ToolExecutionOptimizer()
    return _tool_optimizer
