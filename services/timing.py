import inspect
import logging
import time
from functools import wraps
from typing import Optional
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_timing_enabled() -> bool:
    """Check whether performance timing logs are enabled"""
    return config.ENABLE_TIMING_LOGS


class Timer:
    __slots__ = ("name", "enabled", "start_time", "end_time")

    def __init__(self, name: str):
        self.name = name
        self.enabled = is_timing_enabled()
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def __enter__(self):
        if self.enabled:
            self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.enabled or self.start_time is None:
            return

        self.end_time = time.perf_counter()
        duration = (self.end_time - self.start_time) * 1000
        logger.info(f"⏱️  {self.name}: {duration:.2f}ms")


def timing_decorator(name: str):
    """Decorator for measuring sync or async function execution time"""

    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not is_timing_enabled():
                    return await func(*args, **kwargs)

                start_time = time.perf_counter()
                result = await func(*args, **kwargs)
                duration = (time.perf_counter() - start_time) * 1000
                logger.info(f"⏱️  {name}: {duration:.2f}ms")
                return result

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not is_timing_enabled():
                return func(*args, **kwargs)

            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            duration = (time.perf_counter() - start_time) * 1000
            logger.info(f"⏱️  {name}: {duration:.2f}ms")
            return result

        return sync_wrapper

    return decorator


class RequestTimer:
    __slots__ = ("request_id", "enabled", "start_time", "checkpoints")

    def __init__(self, request_id: Optional[str] = None):
        self.enabled = is_timing_enabled()
        self.request_id = request_id or (str(int(time.time() * 1000)) if self.enabled else "")
        self.start_time = time.perf_counter() if self.enabled else 0.0
        self.checkpoints = []

    def checkpoint(self, name: str):
        if not self.enabled:
            return

        duration = (time.perf_counter() - self.start_time) * 1000
        self.checkpoints.append((name, duration))
        logger.info(f"🔍 [{self.request_id}] {name}: {duration:.2f}ms")

    def summary(self):
        if not self.enabled:
            return

        total_time = (time.perf_counter() - self.start_time) * 1000
        logger.info(f"📊 [{self.request_id}] Total request time: {total_time:.2f}ms")
        logger.info(f"📋 [{self.request_id}] Breakdown:")
        for name, duration in self.checkpoints:
            percentage = (duration / total_time) * 100 if total_time > 0 else 0
            logger.info(f"   - {name}: {duration:.2f}ms ({percentage:.1f}%)")


class TimingControl:
    @staticmethod
    def enable():
        """Enable timing logs at runtime"""
        config.ENABLE_TIMING_LOGS = True
        logger.info("🟢 Timing logs enabled")

    @staticmethod
    def disable():
        """Disable timing logs at runtime"""
        config.ENABLE_TIMING_LOGS = False
        logger.info("🔴 Timing logs disabled")

    @staticmethod
    def toggle():
        """Toggle timing logs status at runtime"""
        if config.ENABLE_TIMING_LOGS:
            TimingControl.disable()
        else:
            TimingControl.enable()

    @staticmethod
    def status() -> bool:
        """Get current timing logs status"""
        status = "enabled" if config.ENABLE_TIMING_LOGS else "disabled"
        logger.info(f"📊 Timing logs are currently {status}")
        return config.ENABLE_TIMING_LOGS

