"""
Interactive dashboard assistant service.

This helper uses the guidance mappings to craft conversational responses and
suggested next steps so users can learn how each diagnostic tool works without
needing to read the docs.
"""

from __future__ import annotations

import os
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

    def answer(self, question: str, tool_hint: str | None = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        text = (question or "").strip()
        if not text:
            return self._default_response()

        context = context or {}
        selected_tool = self._resolve_tool(text, tool_hint) or context.get("tool")

        # Prefer Gemini for all responses when available
        if self.gemini_api_key:
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
        if self.gemini_api_key:
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
        try:
            guidance = self.tools.get(tool) or {}
            prompt = self._build_prompt(question, tool, guidance, context or {})
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.35,
                    "maxOutputTokens": 220,
                },
            }
            resp = requests.post(url, json=payload, timeout=15)
            if resp.status_code != 200:
                logging.getLogger(__name__).warning(
                    "Gemini HTTP %s: %s", resp.status_code, resp.text
                )
                return None
            data = resp.json()
            candidates = data.get("candidates") or []
            if not candidates:
                return None
            text = ""
            for part in candidates[0].get("content", {}).get("parts", []):
                if "text" in part:
                    text += part["text"]
            if not text:
                return None
            # Keep it simple: return the model answer as the main answer, preserve existing tips/actions.
            return {"answer": text.strip(), "ai_provider": "gemini"}
        except Exception:
            logging.getLogger(__name__).warning("Gemini call failed", exc_info=True)
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
                "Respond concisely with 2-4 sentences."
            )

        return (
            f"{base_intro}\n\n"
            f"{context_block}\n"
            f"User question: {question}\n"
            "Respond concisely with 2-4 sentences."
        )
