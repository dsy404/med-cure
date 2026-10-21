import time
import json
import logging
import re
from typing import Optional, Dict, Any, List
import httpx

from ..core.config import settings
from ..schemas.ai import GemmaInterpretation, ComparativeBenchmarkResult
from ..schemas.medicine import SearchResponse, RetrievalMethod
from ..services.normalizer import extract_attributes, normalize_text

logger = logging.getLogger(__name__)

GEMMA_PROMPT_TEMPLATE = """You are a medicine search query interpreter assisting a price transparency engine.
Analyze the following user search query: "{query}"

Output ONLY a single raw JSON object (no markdown, no backticks, no explanations) matching this exact schema:
{{
  "interpreted_name": "<clean medicine name or null>",
  "possible_names": ["<suggested standard spelling or active ingredient>", ...],
  "strength_mentioned": "<strength with unit like 500mg or null>",
  "dosage_form_mentioned": "<e.g. Tablet, Syrup, Injection or null>",
  "missing_attributes": ["strength", "dosage_form", ...],
  "needs_clarification": <true or false>,
  "reason": "<short objective reason>"
}}

STRICT SAFETY RULES:
1. Extract ONLY attributes explicitly stated or obvious typos.
2. DO NOT invent ingredients, strengths, manufacturers, or prices.
3. If the query is ambiguous, set needs_clarification to true.
4. Output raw JSON ONLY.
"""

class GemmaInterpreterService:
    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model_name = model_name or settings.GEMMA_MODEL_NAME
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS
        self._cached_status: Optional[Dict[str, Any]] = None
        self._last_status_check: float = 0.0

    def check_ollama_status(self, force: bool = False) -> Dict[str, Any]:
        """
        Pings Ollama server and lists installed models, with a short TTL cache.
        """
        now = time.time()
        if not force and self._cached_status is not None and (now - self._last_status_check < 5.0):
            return self._cached_status

        self._last_status_check = now
        try:
            with httpx.Client(timeout=0.5) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    has_model = any(self.model_name in m for m in models)
                    self._cached_status = {
                        "ollama_online": True,
                        "available_models": models,
                        "target_model": self.model_name,
                        "target_model_installed": has_model,
                        "status_message": f"Ollama is running with {len(models)} model(s)." if has_model else f"Ollama is running, but model '{self.model_name}' is not pulled yet."
                    }
                    return self._cached_status
        except Exception as e:
            logger.debug(f"Ollama check failed: {e}")

        self._cached_status = {
            "ollama_online": False,
            "available_models": [],
            "target_model": self.model_name,
            "target_model_installed": False,
            "status_message": f"Local Ollama daemon is offline at {self.base_url}. Falling back to deterministic pipeline."
        }
        return self._cached_status

    def interpret_query(self, query: str) -> GemmaInterpretation:
        """
        Sends query to local Gemma model via Ollama.
        Fails safely if Ollama is unreachable or response is malformed.
        """
        clean_query = query.strip()
        start = time.perf_counter()

        # Step 1: Health check
        status = self.check_ollama_status()
        if not status["ollama_online"] or not status["target_model_installed"]:
            exec_time = round((time.perf_counter() - start) * 1000, 2)
            # Safe deterministic extraction without faking AI
            attrs = extract_attributes(clean_query)
            return GemmaInterpretation(
                is_available=False,
                model_name=self.model_name,
                interpreted_name=None,
                possible_names=[],
                strength_mentioned=attrs.strengths[0] if attrs.strengths else None,
                dosage_form_mentioned=attrs.dosage_form,
                missing_attributes=attrs.explicitly_missing_attributes,
                needs_clarification=bool(not attrs.strengths or not attrs.dosage_form),
                reason=status["status_message"],
                execution_time_ms=exec_time
            )

        # Step 2: Inference request
        prompt = GEMMA_PROMPT_TEMPLATE.format(query=clean_query)
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 150
            }
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(f"{self.base_url}/api/generate", json=payload)
                exec_time = round((time.perf_counter() - start) * 1000, 2)

                if res.status_code == 200:
                    raw_text = res.json().get("response", "").strip()
                    # Parse JSON safely
                    try:
                        parsed = json.loads(raw_text)
                    except json.JSONDecodeError:
                        # Extract JSON object with regex if there's surrounding text
                        m = re.search(r"\{.*\}", raw_text, re.DOTALL)
                        if m:
                            parsed = json.loads(m.group(0))
                        else:
                            raise ValueError("Model output did not contain valid JSON.")

                    return GemmaInterpretation(
                        is_available=True,
                        model_name=self.model_name,
                        interpreted_name=parsed.get("interpreted_name"),
                        possible_names=parsed.get("possible_names", []),
                        strength_mentioned=parsed.get("strength_mentioned"),
                        dosage_form_mentioned=parsed.get("dosage_form_mentioned"),
                        missing_attributes=parsed.get("missing_attributes", []),
                        needs_clarification=bool(parsed.get("needs_clarification", True)),
                        reason=parsed.get("reason", "Parsed by local Gemma model"),
                        execution_time_ms=exec_time
                    )
        except Exception as e:
            logger.warning(f"Inference error with Ollama {self.model_name}: {e}")
            exec_time = round((time.perf_counter() - start) * 1000, 2)

        return GemmaInterpretation(
            is_available=False,
            model_name=self.model_name,
            interpreted_name=None,
            possible_names=[],
            strength_mentioned=None,
            dosage_form_mentioned=None,
            missing_attributes=["strength", "dosage_form"],
            needs_clarification=True,
            reason="Local AI inference timed out or failed. Deterministic pipeline in effect.",
            execution_time_ms=round((time.perf_counter() - start) * 1000, 2)
        )
