"""
Interactive dashboard assistant service.

This helper uses the guidance mappings to craft conversational responses and
suggested next steps so users can learn how each diagnostic tool works without
needing to read the docs.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Iterable, List, Optional

import requests
import logging

from .guidance_service import TOOL_GUIDANCE


class DashboardAssistant:
    """
    Simple heuristic assistant that matches user questions to knowledge entries.
    """

    def __init__(self):
        self.tools = TOOL_GUIDANCE
        self.default_actions = [
            "Review /api/tool-guidance?tool=whois to learn how the WHOIS lookup works.",
            "Use /api/domain with a `fields` array to combine multiple tools in one request.",
            "Check the FAQ or documentation panels inside the dashboard for more tips.",
        ]
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        self.gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        # Default to using Gemini whenever a key is present unless explicitly disabled.
        self.gemini_enabled = bool(self.gemini_api_key) and (
            os.environ.get("ASSISTANT_DISABLE_GEMINI", "").lower()
            not in {"1", "true", "yes", "on"}
        )
        # Backoff and circuit breaker knobs to avoid spamming upstream when overloaded.
        self.gemini_max_retries = int(os.environ.get("GEMINI_MAX_RETRIES", "1"))
        self.gemini_retry_backoff = float(os.environ.get("GEMINI_RETRY_BACKOFF", "1.5"))
        self.gemini_circuit_threshold = int(os.environ.get("GEMINI_CIRCUIT_THRESHOLD", "3"))
        self.gemini_circuit_cooldown = int(os.environ.get("GEMINI_CIRCUIT_COOLDOWN", "60"))
        self.gemini_cache_ttl = int(os.environ.get("GEMINI_CACHE_TTL", "900"))
        self.gemini_cache_max = int(os.environ.get("GEMINI_CACHE_MAX", "100"))
        self._gemini_failures = 0
        self._gemini_circuit_until = 0.0
        # Simple in-memory cache to reuse answers for repeated questions/context.
        self._gemini_cache: Dict[tuple, tuple[str, float]] = {}
        # OpenAI (Codex/ChatGPT) configuration
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        self.openai_model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self.openai_enabled = bool(self.openai_api_key) and (
            os.environ.get("ASSISTANT_DISABLE_OPENAI", "").lower()
            not in {"1", "true", "yes", "on"}
        )
        self.openai_max_tokens = int(os.environ.get("OPENAI_MAX_TOKENS", "360"))
        self.openai_temperature = float(os.environ.get("OPENAI_TEMPERATURE", "0.35"))
        self.openai_timeout = int(os.environ.get("OPENAI_TIMEOUT", "12"))
        self.openai_max_retries = int(os.environ.get("OPENAI_MAX_RETRIES", "1"))
        self.openai_retry_backoff = float(os.environ.get("OPENAI_RETRY_BACKOFF", "1.5"))
        self._openai_failures = 0
        self.openai_circuit_threshold = int(os.environ.get("OPENAI_CIRCUIT_THRESHOLD", "3"))
        self.openai_circuit_cooldown = int(os.environ.get("OPENAI_CIRCUIT_COOLDOWN", "60"))
        self._openai_circuit_until = 0.0

    def answer(self, question: str, tool_hint: str | None = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        text = (question or "").strip()
        if not text:
            return self._default_response()

        context = context or {}
        selected_tool = self._resolve_tool(text, tool_hint) or context.get("tool")

        # Prefer OpenAI if enabled; otherwise Gemini; otherwise deterministic guidance.
        if self._is_openai_active():
            cached_ai = self._cache_get(question=text, tool=selected_tool, context=context)
            if cached_ai and cached_ai.get("answer"):
                if selected_tool:
                    return self._build_ai_tool_response(selected_tool, cached_ai["answer"], context)
                return self._build_ai_general_response(cached_ai["answer"], context)
            for attempt_tool in (selected_tool, None, selected_tool):
                ai_response = self._call_openai(question=text, tool=attempt_tool, context=context)
                if ai_response and ai_response.get("answer"):
                    if attempt_tool:
                        return self._build_ai_tool_response(attempt_tool, ai_response["answer"], context)
                    return self._build_ai_general_response(ai_response["answer"], context)
            # OpenAI configured but unavailable; try Gemini next.

        if self._is_gemini_active():
            cached_ai = self._cache_get(question=text, tool=selected_tool, context=context)
            if cached_ai and cached_ai.get("answer"):
                if selected_tool:
                    return self._build_ai_tool_response(selected_tool, cached_ai["answer"], context)
                return self._build_ai_general_response(cached_ai["answer"], context)
            for attempt_tool in (selected_tool, None, selected_tool):
                ai_response = self._call_gemini(question=text, tool=attempt_tool, context=context)
                if ai_response and ai_response.get("answer"):
                    if attempt_tool:
                        return self._build_ai_tool_response(attempt_tool, ai_response["answer"], context)
                    return self._build_ai_general_response(ai_response["answer"], context)
            # Gemini configured but unavailable after retries
            return self._fallback_unavailable()

        # Fallback to deterministic guidance when Gemini is not configured or fails
        if selected_tool:
            return self._build_tool_response(selected_tool, text, context)

        return self._default_response()

    def _resolve_tool(self, text: str, tool_hint: str | None) -> Optional[str]:
        normalized_hint = (tool_hint or "").strip().lower()
        if normalized_hint and normalized_hint in self.tools:
            return normalized_hint

        text_lower = text.lower()
        best_tool = None
        best_score = 0
        for key, guidance in self.tools.items():
            score = 0
            if key in text_lower:
                score += 3
            keywords = guidance.get("keywords", [])
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            if score > best_score:
                best_score = score
                best_tool = key

        return best_tool if best_score > 0 else None

    def _build_tool_response(self, tool: str, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        guidance = self.tools[tool]
        context_line = self._context_line(context)
        answer = (
            f"{guidance['title']} helps with {guidance['description'].lower()} "
            f"Ask for more details or use {guidance['example']}."
        )
        if context_line:
            answer = f"{context_line} {answer}"
        return {
            "tool": tool,
            "answer": answer,
            "tips": guidance.get("usage", []),
            "example": guidance.get("example"),
            "suggested_actions": self._build_suggestions(tool),
            "confidence": f"{min(95, 50 + len(guidance.get('usage', [])) * 10)}%",
            "context": context or None,
        }

    def _build_suggestions(self, tool: str) -> List[str]:
        guidance = self.tools[tool]
        actions = [
            f"Call `/api/tool-guidance?tool={tool}` for step-by-step usage.",
            guidance.get("example"),
        ]
        if tool == "domain":
            actions.append("Include the `fields` payload to filter the diagnostics you need.")
        return [action for action in actions if action]

    def _default_response(self) -> Dict[str, Any]:
        if self._is_gemini_active():
            ai_response = self._call_gemini(
                question="Briefly introduce how you can help with IT, systems, and networking questions.",
                tool=None,
                context={},
            )
            if ai_response and ai_response.get("answer"):
                return self._build_ai_general_response(ai_response["answer"], {})

        return self._fallback_unavailable()

    def _build_ai_tool_response(self, tool: str, ai_answer: str, context: Dict[str, Any]) -> Dict[str, Any]:
        guidance = self.tools[tool]
        return {
            "tool": tool,
            "answer": ai_answer.strip(),
            "tips": guidance.get("usage", []),
            "example": guidance.get("example"),
            "suggested_actions": self._build_suggestions(tool),
            "confidence": "92%",
            "context": context or None,
        }

    def _build_ai_general_response(self, ai_answer: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "answer": ai_answer.strip(),
            "suggested_actions": self.default_actions,
            "confidence": "90%",
            "context": context or None,
        }

    def _fallback_unavailable(self) -> Dict[str, Any]:
        return {
            "answer": "I’m having trouble reaching the assistant right now. Please try again in a moment.",
            "suggested_actions": self.default_actions,
            "confidence": "0%",
            "available_tools": sorted(self.tools.keys()),
        }

    def _context_line(self, context: Dict[str, Any]) -> str:
        if not context:
            return ""
        parts = []
        tool = context.get("tool")
        target = context.get("target")
        summary = context.get("summary")
        if tool:
            parts.append(f"Latest {tool.replace('_', ' ')}")
        if target:
            parts.append(f"on {target}")
        if summary:
            parts.append(f"({summary})")
        return " ".join(parts).strip()

    def _call_gemini(self, question: str, tool: Optional[str], context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Optional Gemini call; returns None on any failure."""
        if not self._is_gemini_active():
            return None
        now = time.time()
        if now < self._gemini_circuit_until:
            return None
        try:
            guidance = self.tools.get(tool) or {}
            prompt = self._build_prompt(question, tool, guidance, context or {})
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.35,
                    "maxOutputTokens": 360,
                },
            }
            for attempt in range(1, self.gemini_max_retries + 1):
                resp = requests.post(url, json=payload, timeout=12)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates") or []
                    if not candidates:
                        break
                    text = ""
                    for part in candidates[0].get("content", {}).get("parts", []):
                        if "text" in part:
                            text += part["text"]
                    if not text:
                        break
                    # Success: reset failure counters and return the model answer.
                    self._gemini_failures = 0
                    answer = text.strip()
                    self._cache_set(question=question, tool=tool, context=context, answer=answer)
                    return {"answer": answer, "ai_provider": "gemini"}

                # Log once per attempt with status code to aid debugging.
                logging.getLogger(__name__).warning("Gemini HTTP %s: %s", resp.status_code, resp.text)
                if resp.status_code >= 500:
                    self._gemini_failures += 1
                    # Fail fast on overload and open circuit sooner when we keep seeing 503s.
                    if resp.status_code == 503:
                        if self._gemini_failures >= self.gemini_circuit_threshold:
                            self._gemini_circuit_until = time.time() + self.gemini_circuit_cooldown
                            logging.getLogger(__name__).warning(
                                "Gemini circuit open for %ss after %s failures",
                                self.gemini_circuit_cooldown,
                                self._gemini_failures,
                            )
                        return None
                if attempt < self.gemini_max_retries:
                    time.sleep(self.gemini_retry_backoff * attempt)

            # If we exhaust retries or get a non-success, consider circuit breaking.
            if self._gemini_failures >= self.gemini_circuit_threshold:
                self._gemini_circuit_until = time.time() + self.gemini_circuit_cooldown
                logging.getLogger(__name__).warning(
                    "Gemini circuit open for %ss after %s failures",
                    self.gemini_circuit_cooldown,
                    self._gemini_failures,
                )
            return None
        except Exception:
            self._gemini_failures += 1
            logging.getLogger(__name__).warning("Gemini call failed", exc_info=True)
            if self._gemini_failures >= self.gemini_circuit_threshold:
                self._gemini_circuit_until = time.time() + self.gemini_circuit_cooldown
                logging.getLogger(__name__).warning(
                    "Gemini circuit open for %ss after exception failures",
                    self.gemini_circuit_cooldown,
                )
            return None

    def _is_gemini_active(self) -> bool:
        """Use Gemini whenever a key is present, unless explicitly disabled or circuit-open."""
        return bool(self.gemini_enabled and self.gemini_api_key)

    def _is_openai_active(self) -> bool:
        """Use OpenAI whenever a key is present, unless explicitly disabled or circuit-open."""
        return bool(self.openai_enabled and self.openai_api_key and time.time() >= self._openai_circuit_until)

    def _normalize_question(self, question: str) -> str:
        return " ".join(question.lower().split())

    def _cache_key(self, question: str, tool: Optional[str], context: Optional[Dict[str, Any]]) -> tuple:
        context_line = self._context_line(context or {})
        return (tool or "", context_line, self._normalize_question(question))

    def _cache_get(self, question: str, tool: Optional[str], context: Optional[Dict[str, Any]]) -> Optional[Dict[str, str]]:
        key = self._cache_key(question, tool, context)
        entry = self._gemini_cache.get(key)
        if not entry:
            return None
        answer, ts = entry
        if (time.time() - ts) > self.gemini_cache_ttl:
            self._gemini_cache.pop(key, None)
            return None
        return {"answer": answer, "ai_provider": "gemini-cache"}

    def _cache_set(self, question: str, tool: Optional[str], context: Optional[Dict[str, Any]], answer: str) -> None:
        if not answer:
            return
        key = self._cache_key(question, tool, context)
        self._gemini_cache[key] = (answer, time.time())
        if len(self._gemini_cache) > self.gemini_cache_max:
            # Evict the oldest entry to cap memory.
            oldest_key = min(self._gemini_cache.items(), key=lambda item: item[1][1])[0]
            if oldest_key != key:
                self._gemini_cache.pop(oldest_key, None)

    def _call_openai(self, question: str, tool: Optional[str], context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Call OpenAI (Codex/ChatGPT) API; returns None on any failure."""
        if not self._is_openai_active():
            return None
        now = time.time()
        if now < self._openai_circuit_until:
            return None
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }
        try:
            guidance = self.tools.get(tool) or {}
            prompt = self._build_prompt(question, tool, guidance, context or {})
            payload = {
                "model": self.openai_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": self.openai_max_tokens,
                "temperature": self.openai_temperature,
            }
            for attempt in range(1, self.openai_max_retries + 1):
                resp = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.openai_timeout,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices") or []
                    if not choices or not choices[0].get("message", {}).get("content"):
                        break
                    answer = choices[0]["message"]["content"].strip()
                    self._openai_failures = 0
                    self._cache_set(question=question, tool=tool, context=context, answer=answer)
                    return {"answer": answer, "ai_provider": "openai"}
                logging.getLogger(__name__).warning("OpenAI HTTP %s: %s", resp.status_code, resp.text)
                if resp.status_code >= 500:
                    self._openai_failures += 1
                    if resp.status_code == 503 and self._openai_failures >= self.openai_circuit_threshold:
                        self._openai_circuit_until = time.time() + self.openai_circuit_cooldown
                        logging.getLogger(__name__).warning(
                            "OpenAI circuit open for %ss after %s failures",
                            self.openai_circuit_cooldown,
                            self._openai_failures,
                        )
                        return None
                if attempt < self.openai_max_retries:
                    time.sleep(self.openai_retry_backoff * attempt)
            if self._openai_failures >= self.openai_circuit_threshold:
                self._openai_circuit_until = time.time() + self.openai_circuit_cooldown
                logging.getLogger(__name__).warning(
                    "OpenAI circuit open for %ss after %s failures",
                    self.openai_circuit_cooldown,
                    self._openai_failures,
                )
            return None
        except Exception:
            self._openai_failures += 1
            logging.getLogger(__name__).warning("OpenAI call failed", exc_info=True)
            if self._openai_failures >= self.openai_circuit_threshold:
                self._openai_circuit_until = time.time() + self.openai_circuit_cooldown
                logging.getLogger(__name__).warning(
                    "OpenAI circuit open for %ss after exception failures",
                    self.openai_circuit_cooldown,
                )
            return None

    def _build_prompt(self, question: str, tool: Optional[str], guidance: Dict[str, Any], context: Dict[str, Any]) -> str:
        usage = "\n".join(f"- {item}" for item in guidance.get("usage", []))
        example = guidance.get("example", "")
        description = guidance.get("description", "")
        suggested = "\n".join(f"- {action}" for action in (self._build_suggestions(tool) if tool else []))
        context_line = self._context_line(context)
        context_block = f"\nRecent context: {context_line}" if context_line else ""

        base_intro = (
            "You are a knowledgeable teacher and technical expert specializing in IT, computer systems, and networking. "
            "You are helping a user inside the Vantage dashboard, which offers WHOIS, DNS records, IP Geolocation, Port Scan, Speed Test, and a combined Domain Research tool. "
            "Explain the 'why' and 'how' behind technical topics, keep advice actionable, and offer practice questions when helpful. "
            "If a question is unrelated to IT or networking, politely state your scope."
        )

        if tool:
            return (
                f"{base_intro}\n\n"
                f"Selected tool: {tool}\n"
                f"Description: {description}\n"
                f"Usage tips:\n{usage}\n"
                f"Example call: {example}\n"
                f"Suggested actions:\n{suggested}\n"
                f"{context_block}\n\n"
                f"User question: {question}\n"
                "Respond with clear steps and explanation; expand with examples when helpful (up to ~6 sentences)."
            )

        return (
            f"{base_intro}\n\n"
            f"{context_block}\n"
            f"User question: {question}\n"
            "Respond with clear steps and explanation; expand with examples when helpful (up to ~6 sentences)."
        )
