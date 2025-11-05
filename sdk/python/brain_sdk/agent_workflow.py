import asyncio
import inspect
from typing import Any, Callable

from brain_sdk.logger import log_debug


class AgentWorkflow:
    """
    Minimal execution helper that keeps the agent API stable while the backend
    handles run tracking. All network-based workflow updates have been removed.
    """

    def __init__(self, agent_instance):
        self.agent = agent_instance

    def replace_function_references(self, original_func: Callable, tracked_func: Callable, func_name: str) -> None:
        """Replace the agent attribute with the tracked wrapper."""
        setattr(self.agent, func_name, tracked_func)

    async def execute_with_tracking(self, original_func: Callable, args: tuple, kwargs: dict) -> Any:
        """
        Execute the wrapped function, awaiting the result when necessary.

        The Brain backend now records executions directly, so no additional
        registration or notification is required here.
        """

        try:
            result = original_func(*args, **kwargs)
            if inspect.isawaitable(result):
                return await result
            if asyncio.iscoroutine(result):
                return await result
            return result
        except Exception:
            if getattr(self.agent, "dev_mode", False):
                log_debug("AgentWorkflow caught exception during execution", exc_info=True)
            raise

    async def notify_call_start(self, *args, **kwargs) -> None:
        """No-op placeholder for legacy callers."""
        return None

    async def notify_call_complete(self, *args, **kwargs) -> None:
        """No-op placeholder for legacy callers."""
        return None

    async def notify_call_error(self, *args, **kwargs) -> None:
        """No-op placeholder for legacy callers."""
        return None
