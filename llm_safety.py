"""
LLM Safety Wrapper with Timeout and Circuit Breaker
Prevents cascading failures and ensures <2s response time
ELITE REFINEMENT: Module-specific circuit breakers
"""

import asyncio
import time
import random
import logging
from typing import Optional, Callable, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMCircuitBreaker:
    """
    Circuit breaker for LLM calls.
    Disables LLM for 60s after 3 failures within 60s window.
    """

    def __init__(self, name: str = "default"):
        self.name = name
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.disabled_until: Optional[float] = None

        # Configuration - HACKATHON: More forgiving thresholds for HF infrastructure
        self.MAX_FAILURES = 5  # Increased from 3 to 5
        self.FAILURE_WINDOW = 90  # Increased from 60 to 90 seconds
        self.COOLDOWN_PERIOD = 30  # Reduced from 60 to 30 seconds

    def should_allow_llm(self) -> bool:
        """Check if LLM calls are allowed."""
        now = time.time()

        # Check if in cooldown period
        if self.disabled_until and now < self.disabled_until:
            return False

        # Reset if cooldown expired
        if self.disabled_until and now >= self.disabled_until:
            self.reset()
            logger.info(f"🔄 Circuit breaker [{self.name}] reset - LLM re-enabled")

        return True

    def record_failure(self) -> None:
        """Record an LLM failure."""
        now = time.time()

        # Reset counter if last failure was outside window
        if self.last_failure_time and (now - self.last_failure_time) > self.FAILURE_WINDOW:
            self.failure_count = 0

        self.failure_count += 1
        self.last_failure_time = now

        # Trip circuit breaker if threshold exceeded
        if self.failure_count >= self.MAX_FAILURES:
            self.disabled_until = now + self.COOLDOWN_PERIOD
            logger.warning(
                f"⚠️ [LLM BREAKER] [{self.name}] TRIPPED - disabled for {self.COOLDOWN_PERIOD}s "
                f"(failures: {self.failure_count})"
            )

    def record_success(self) -> None:
        """Record successful LLM call."""
        # Gradually decrease failure count on success
        if self.failure_count > 0:
            self.failure_count = max(0, self.failure_count - 1)

    def reset(self) -> None:
        """Reset circuit breaker."""
        self.failure_count = 0
        self.last_failure_time = None
        self.disabled_until = None


# ELITE REFINEMENT: Module-specific circuit breakers
classifier_breaker = LLMCircuitBreaker("classifier")
generator_breaker = LLMCircuitBreaker("generator")
extractor_breaker = LLMCircuitBreaker("extractor")

# Map operation types to their breakers
_breaker_map = {
    "classifier": classifier_breaker,
    "classification": classifier_breaker,
    "scam_classifier": classifier_breaker,
    "generator": generator_breaker,
    "response_generator": generator_breaker,
    "response": generator_breaker,
    "extractor": extractor_breaker,
    "extraction": extractor_breaker,
    "layer2": extractor_breaker
}


def _get_breaker_for_operation(operation_name: str) -> LLMCircuitBreaker:
    """Get appropriate circuit breaker for operation."""
    operation_lower = operation_name.lower()
    for key, breaker in _breaker_map.items():
        if key in operation_lower:
            return breaker
    # Default fallback
    return classifier_breaker


async def safe_llm_call(
    llm_func: Callable,
    timeout: float,
    fallback_value: Any,
    operation_name: str = "LLM call",
    *args,
    **kwargs
) -> Any:
    """
    Safe wrapper for LLM calls with timeout and module-specific circuit breaker.
    ELITE REFINEMENT: Adds 10-30ms jitter to spread concurrent load.

    Args:
        llm_func: Async function to call
        timeout: Timeout in seconds
        fallback_value: Value to return on failure
        operation_name: Name for logging (determines which breaker to use)
        *args, **kwargs: Arguments to pass to llm_func

    Returns:
        Result from llm_func or fallback_value on failure
    """

    # Get appropriate circuit breaker
    breaker = _get_breaker_for_operation(operation_name)

    # Check circuit breaker
    if not breaker.should_allow_llm():
        logger.warning(f"⚠️ [LLM BREAKER] {operation_name} skipped - [{breaker.name}] module disabled")
        # Log performance metrics
        try:
            from performance_logger import performance_logger
            performance_logger.log_llm_call(breaker.name, False, 0, "circuit_breaker_open")
        except:
            pass
        return fallback_value

    start_time = time.time()
    
    try:
        # ELITE REFINEMENT: Add jitter to spread concurrent load
        jitter = random.uniform(0.01, 0.03)  # 10-30ms
        await asyncio.sleep(jitter)

        # Execute with timeout
        result = await asyncio.wait_for(
            llm_func(*args, **kwargs),
            timeout=timeout
        )

        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000

        # Record success
        breaker.record_success()
        
        # Log performance metrics
        try:
            from performance_logger import performance_logger
            performance_logger.log_llm_call(breaker.name, True, response_time_ms, None)
        except:
            pass

        return result

    except asyncio.TimeoutError:
        response_time_ms = (time.time() - start_time) * 1000
        logger.warning(f"⏱️ {operation_name} timeout after {timeout}s - using fallback")
        breaker.record_failure()
        
        # Log performance metrics
        try:
            from performance_logger import performance_logger
            performance_logger.log_llm_call(breaker.name, False, response_time_ms, "timeout")
        except:
            pass
        
        return fallback_value

    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000
        logger.error(f"❌ {operation_name} error: {e} - using fallback")
        breaker.record_failure()
        
        # Log performance metrics
        try:
            from performance_logger import performance_logger
            performance_logger.log_llm_call(breaker.name, False, response_time_ms, str(e)[:100])
        except:
            pass
        
        return fallback_value


def is_llm_available(module: str = "all") -> bool:
    """
    Check if LLM is currently available.

    Args:
        module: "all", "classifier", "generator", or "extractor"

    Returns:
        True if module is available
    """
    if module == "all":
        return (classifier_breaker.should_allow_llm() and
                generator_breaker.should_allow_llm() and
                extractor_breaker.should_allow_llm())

    breaker = _get_breaker_for_operation(module)
    return breaker.should_allow_llm()
