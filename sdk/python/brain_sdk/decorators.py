"""
Enhanced decorators for Brain SDK with automatic workflow tracking.
Provides always-on workflow tracking for reasoner calls.
"""

import asyncio
import functools
import inspect
from typing import List, Union, Callable, Optional, Any

from brain_sdk.logger import log_warn

from .execution_context import (
    ExecutionContext,
    get_current_context,
    set_execution_context,
    reset_execution_context,
)
from .agent_registry import get_current_agent_instance
from .types import ReasonerDefinition, SkillDefinition
from .pydantic_utils import convert_function_args, should_convert_args
from pydantic import ValidationError


def reasoner(func=None, *, 
             path: Optional[str] = None,
             tags: Optional[List[str]] = None,
             description: Optional[str] = None,
             track_workflow: bool = True,
             **kwargs):
    """
    Enhanced reasoner decorator with automatic workflow tracking and full feature support.
    
    Supports both:
    @reasoner                           # Default: track_workflow=True
    @reasoner(track_workflow=False)     # Explicit: disable tracking
    @reasoner(path="/custom/path")      # Custom endpoint path
    @reasoner(tags=["ai", "nlp"])       # Tags for organization
    @reasoner(description="...")        # Custom description
    
    Args:
        func: The function to decorate (when used without parentheses)
        path: Custom API endpoint path for this reasoner
        tags: List of tags for organizing and categorizing reasoners
        description: Description of what this reasoner does
        track_workflow: Whether to enable automatic workflow tracking (default: True)
        **kwargs: Additional metadata to store with the reasoner
    
    Returns:
        Decorated function with workflow tracking capabilities and full metadata support
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        async def wrapper(*args, **kwargs):
            if track_workflow:
                # Execute with automatic workflow tracking
                return await _execute_with_tracking(f, *args, **kwargs)
            else:
                # Execute without tracking
                if asyncio.iscoroutinefunction(f):
                    return await f(*args, **kwargs)
                else:
                    return f(*args, **kwargs)
        
        # Store comprehensive metadata on the function
        wrapper._is_reasoner = True
        wrapper._track_workflow = track_workflow
        wrapper._reasoner_name = f.__name__
        wrapper._original_func = f
        wrapper._reasoner_path = path
        wrapper._reasoner_tags = tags or []
        wrapper._reasoner_description = description or f.__doc__ or f"Reasoner: {f.__name__}"
        
        # Store any additional metadata
        for key, value in kwargs.items():
            setattr(wrapper, f"_reasoner_{key}", value)
        
        return wrapper
    
    # Handle both @reasoner and @reasoner(...) syntax
    if func is None:
        # Called as @reasoner(track_workflow=False) or @reasoner(path="/custom")
        return decorator
    else:
        # Called as @reasoner (no parentheses)
        return decorator(func)


async def _execute_with_tracking(func: Callable, *args, **kwargs) -> Any:
    """
    Core function that handles automatic workflow tracking for reasoner calls.
    
    Args:
        func: The reasoner function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        The result of the function execution
    """
    # Get current execution context
    current_context = get_current_context()
    
    # Get agent instance (from context or global registry)
    agent_instance = get_current_agent_instance()
    
    if not agent_instance:
        # No agent context - execute without tracking
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    # Generate execution metadata
    # Build a child context when executing under an existing workflow; otherwise create a root context
    if current_context:
        execution_context = current_context.create_child_context()
        execution_context.reasoner_name = func.__name__
        parent_context = current_context
    else:
        workflow_name = func.__name__
        if hasattr(agent_instance, "node_id"):
            workflow_name = f"{agent_instance.node_id}_{workflow_name}"
        execution_context = ExecutionContext.new_root(
            agent_node_id=getattr(agent_instance, "node_id", "agent"),
            reasoner_name=workflow_name,
        )
        execution_context.reasoner_name = func.__name__
        execution_context.agent_instance = agent_instance
        parent_context = None

    # Align run/session metadata with the parent context so registration inherits the workflow run
    if parent_context:
        execution_context.run_id = parent_context.run_id
        execution_context.session_id = parent_context.session_id
        execution_context.caller_did = parent_context.caller_did
        execution_context.target_did = parent_context.target_did
        execution_context.agent_node_did = parent_context.agent_node_did

    previous_agent_context = getattr(agent_instance, "_current_execution_context", None)
    agent_instance._current_execution_context = execution_context

    input_data = {"args": args, "kwargs": kwargs}

    try:
        # Execute function with new context
        token = set_execution_context(execution_context)
        try:
            # Inject execution_context if the function accepts it
            sig = inspect.signature(func)
            if "execution_context" in sig.parameters:
                kwargs["execution_context"] = execution_context
            
            # 🔥 NEW: Automatic Pydantic model conversion (FastAPI-like behavior)
            try:
                if should_convert_args(func):
                    converted_args, converted_kwargs = convert_function_args(func, args, kwargs)
                    args = converted_args
                    kwargs = converted_kwargs
            except ValidationError as e:
                # Re-raise validation errors with context
                raise ValidationError(
                    f"Pydantic validation failed for reasoner '{func.__name__}': {e}",
                    model=getattr(e, 'model', None)
                ) from e
            except Exception as e:
                # Log conversion errors but continue with original args for backward compatibility
                if hasattr(agent_instance, 'dev_mode') and agent_instance.dev_mode:
                    log_warn(f"Failed to convert arguments for {func.__name__}: {e}")
            
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
        finally:
            reset_execution_context(token)
            agent_instance._current_execution_context = previous_agent_context

        return result
def on_change(pattern: Union[str, List[str]]):
    """
    Decorator to mark a function as a memory event listener.
    
    Args:
        pattern: Memory pattern(s) to listen for changes
        
    Returns:
        Decorated function with memory event listener metadata
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        # Attach metadata to the function
        wrapper._memory_event_listener = True
        wrapper._memory_event_patterns = pattern if isinstance(pattern, list) else [pattern]
        return wrapper
    return decorator


# Legacy support for old reasoner decorator signature
def legacy_reasoner(reasoner_id: str, input_schema: dict, output_schema: dict):
    """
    Legacy reasoner decorator for backward compatibility.
    
    This is kept for compatibility with existing code that uses the old signature.
    New code should use the enhanced @reasoner decorator.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Attach metadata to the function
        wrapper._reasoner_def = ReasonerDefinition(
            id=reasoner_id,
            input_schema=input_schema,
            output_schema=output_schema
        )
        return wrapper
    return decorator
