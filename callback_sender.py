"""
callback_sender.py — POST finalOutput to the GUVI session log endpoint.

Retry policy: 3 attempts with 2-second delay between each.
The callback is fired as a background task (asyncio.create_task) from main.py
AFTER the final HTTP response has been sent to the platform, avoiding timeouts.

Only sends once per session (callback_sent flag checked by main.py).
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CALLBACK_RETRY_COUNT = 3
CALLBACK_RETRY_DELAY = 2   # seconds between retries


# ---------------------------------------------------------------------------
# CallbackSender
# ---------------------------------------------------------------------------

class CallbackSender:

    def __init__(self) -> None:
        self.callback_url: str = os.getenv("CALLBACK_URL", "")
        # httpx is imported lazily to keep startup fast
        self._httpx_available: Optional[bool] = None

    # ── Primary send method ──────────────────────────────────────────────────

    async def send_final_output(
        self,
        session_id: str,
        payload: Dict[str, Any],
        url: Optional[str] = None,
    ) -> bool:
        """
        POST the finalOutput payload to the GUVI session log endpoint.
        `url` overrides the CALLBACK_URL env var (use when GUVI sends callbackUrl in request).
        Retries up to CALLBACK_RETRY_COUNT times on failure.
        Returns True on success, False if all attempts fail.
        """
        effective_url = url or self.callback_url
        if not effective_url:
            logger.warning(
                f"[{session_id}] CALLBACK_URL not configured — skipping callback. "
                "Set CALLBACK_URL in your .env file or ensure GUVI sends callbackUrl."
            )
            return False
        # Temporarily override so _try_with_httpx / _try_with_urllib use it
        original_url = self.callback_url
        self.callback_url = effective_url
        try:
            return await self._do_send(session_id, payload)
        finally:
            self.callback_url = original_url

    async def _do_send(
        self,
        session_id: str,
        payload: Dict[str, Any],
    ) -> bool:
        """Internal: perform the actual HTTP POST (called after URL is set)."""
        if not payload:
            logger.error(f"[{session_id}] Empty finalOutput payload — callback aborted.")
            return False

        # Log what we're about to send
        logger.info(
            f"[{session_id}] Sending finalOutput to {self.callback_url} "
            f"(scamDetected={payload.get('scamDetected')}, "
            f"turns={payload.get('totalMessagesExchanged', 0) // 2}, "
            f"intel_items={self._count_intel(payload)})"
        )

        if await self._try_with_httpx(session_id, payload):
            return True

        # httpx failed or unavailable — try with urllib (stdlib fallback)
        return await self._try_with_urllib(session_id, payload)

    # ── httpx implementation (preferred) ────────────────────────────────────

    async def _try_with_httpx(
        self,
        session_id: str,
        payload: Dict[str, Any],
    ) -> bool:
        try:
            import httpx
        except ImportError:
            logger.warning("httpx not installed — falling back to urllib")
            return False

        api_key = os.getenv("HONEYPOT_API_KEY", "")
        headers = {
            "Content-Type": "application/json",
            "X-Session-ID": session_id,
        }
        if api_key:
            headers["x-api-key"] = api_key

        for attempt in range(1, CALLBACK_RETRY_COUNT + 1):
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.post(
                        self.callback_url,
                        json=payload,
                        headers=headers,
                    )

                if response.status_code in (200, 201, 202, 204):
                    logger.info(
                        f"[{session_id}] Callback SUCCESS (attempt {attempt}) "
                        f"— HTTP {response.status_code}"
                    )
                    return True
                else:
                    logger.warning(
                        f"[{session_id}] Callback HTTP {response.status_code} "
                        f"(attempt {attempt}): {response.text[:200]}"
                    )

            except httpx.TimeoutException:
                logger.warning(f"[{session_id}] Callback timeout (attempt {attempt})")
            except httpx.ConnectError as e:
                logger.warning(f"[{session_id}] Callback connect error (attempt {attempt}): {e}")
            except Exception as e:
                logger.error(f"[{session_id}] Callback unexpected error (attempt {attempt}): {e}")

            if attempt < CALLBACK_RETRY_COUNT:
                await asyncio.sleep(CALLBACK_RETRY_DELAY)

        logger.error(
            f"[{session_id}] All {CALLBACK_RETRY_COUNT} callback attempts failed (httpx)."
        )
        return False

    # ── urllib fallback (no external dependencies) ────────────────────────────

    async def _try_with_urllib(
        self,
        session_id: str,
        payload: Dict[str, Any],
    ) -> bool:
        import urllib.request
        import urllib.error

        api_key = os.getenv("HONEYPOT_API_KEY", "")
        data    = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "X-Session-ID": session_id,
        }
        if api_key:
            headers["x-api-key"] = api_key

        for attempt in range(1, CALLBACK_RETRY_COUNT + 1):
            try:
                req = urllib.request.Request(
                    self.callback_url,
                    data=data,
                    headers=headers,
                    method="POST",
                )
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: urllib.request.urlopen(req, timeout=15),
                )
                status = response.getcode()
                if status in (200, 201, 202, 204):
                    logger.info(
                        f"[{session_id}] Callback SUCCESS via urllib (attempt {attempt}) "
                        f"— HTTP {status}"
                    )
                    return True

            except urllib.error.HTTPError as e:
                logger.warning(
                    f"[{session_id}] urllib HTTP error (attempt {attempt}): {e.code} {e.reason}"
                )
            except urllib.error.URLError as e:
                logger.warning(
                    f"[{session_id}] urllib URL error (attempt {attempt}): {e.reason}"
                )
            except Exception as e:
                logger.error(f"[{session_id}] urllib unexpected error (attempt {attempt}): {e}")

            if attempt < CALLBACK_RETRY_COUNT:
                await asyncio.sleep(CALLBACK_RETRY_DELAY)

        logger.error(
            f"[{session_id}] All {CALLBACK_RETRY_COUNT} callback attempts failed (urllib)."
        )
        return False

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _count_intel(payload: Dict[str, Any]) -> int:
        intel = payload.get("extractedIntelligence", {})
        return sum(len(v) for v in intel.values() if isinstance(v, list))


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
callback_sender = CallbackSender()
