"""Model router to centralize LLM calls and provide fallbacks (Bedrock → SageMaker/AutoML)."""

import json
import logging
import os
from typing import Any, Optional

import boto3

logger = logging.getLogger(__name__)


class ModelRouter:
    """Adapter that exposes a Bedrock-compatible surface but can fall back to
    SageMaker or an AutoML endpoint when configured.

    Behavior is controlled by environment variables:
    - ONLY_AWS_OUTPUTS: when true, prefer Bedrock and enforce bedrock-like model ids
    - ALLOW_SAGEMAKER_FALLBACK: when true and a SAGEMAKER_ENDPOINT_NAME is set, use it on Bedrock failures
    - SAGEMAKER_ENDPOINT_NAME: name of the SageMaker endpoint to invoke for fallback
    - AUTOML_ENDPOINT_NAME: optional AutoML endpoint name (treated like SageMaker)
    """

    def __init__(self, region: Optional[str] = None) -> None:
        self.region = region or os.getenv("AWS_REGION", "ap-south-1")
        self._bedrock = None
        self._bedrock_error: Optional[Exception] = None
        self.local_mode = os.getenv("USE_LOCAL_MODELS", "false").lower() in ("1", "true", "yes")
        if self.local_mode:
            logger.info("ModelRouter: running in local mock mode (USE_LOCAL_MODELS=true)")
            # Do not attempt to initialise Bedrock or SageMaker in local mock mode
            self._bedrock = None
            self._bedrock_error = None
            self.allow_sagemaker = False
            self.sagemaker_endpoint = None
            self.automl_endpoint = None
            return
        try:
            from src.shared.aws_clients.bedrock_client import BedrockClient

            self._bedrock = BedrockClient(region=self.region)
            logger.info("ModelRouter: using BedrockClient")
        except Exception as e:  # pragma: no cover - defensive
            self._bedrock_error = e
            logger.warning(f"ModelRouter: BedrockClient init failed: {e}")

        self.allow_sagemaker = os.getenv("ALLOW_SAGEMAKER_FALLBACK", "false").lower() in ("1", "true", "yes")
        self.sagemaker_endpoint = os.getenv("SAGEMAKER_ENDPOINT_NAME")
        self.automl_endpoint = os.getenv("AUTOML_ENDPOINT_NAME")

    def _local_response(self, prompt: str, kind: str = "text") -> str:
        """Return a deterministic mock response for local testing."""
        if kind == "summary":
            # Return a concise summary-like string
            head = prompt.strip().split("\n\n")[-1][:200]
            return f"Mock summary: {head[:150]}..."
        if kind == "vision":
            return "Mock vision: detected text and metadata"
        # Generic mock for text generation
        s = prompt.strip().replace("\n", " ")
        return f"MOCK_RESPONSE: {s[:400]}"

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _invoke_sagemaker_endpoint(self, endpoint_name: str, payload: Any) -> str:
        """Invoke a SageMaker/AutoML endpoint. Treats response body as plain text."""
        client = boto3.client("sagemaker-runtime", region_name=self.region)
        body = json.dumps(payload) if not isinstance(payload, (bytes, str)) else (payload if isinstance(payload, str) else payload.decode())
        resp = client.invoke_endpoint(EndpointName=endpoint_name, ContentType="application/json", Body=body)
        # Response body is a streaming object
        if hasattr(resp["Body"], "read"):
            raw = resp["Body"].read()
            try:
                return raw.decode("utf-8")
            except Exception:
                return str(raw)
        return str(resp.get("Body", ""))

    def _sagemaker_fallback(self, prompt: str) -> str:
        if self.allow_sagemaker and self.sagemaker_endpoint:
            logger.info("ModelRouter: falling back to SageMaker endpoint")
            try:
                return self._invoke_sagemaker_endpoint(self.sagemaker_endpoint, {"input": prompt})
            except Exception as e:
                logger.error(f"SageMaker fallback failed: {e}")
                raise
        if self.automl_endpoint:
            logger.info("ModelRouter: falling back to AutoML endpoint")
            try:
                return self._invoke_sagemaker_endpoint(self.automl_endpoint, {"input": prompt})
            except Exception as e:
                logger.error(f"AutoML fallback failed: {e}")
                raise
        raise RuntimeError("No fallback endpoint configured for SageMaker/AutoML")

    # ──────────────────────────────────────────────────────────────────────────
    # Public surface — mirror BedrockClient API
    # ──────────────────────────────────────────────────────────────────────────

    def invoke_model(self, model_id: str, prompt: str, **kwargs: Any) -> str:
        """Invoke the preferred provider's model. Falls back to SageMaker/AutoML when configured."""
        # Local mock mode
        if getattr(self, "local_mode", False):
            return self._local_response(prompt)

        # Try Bedrock first if available
        if self._bedrock is not None:
            try:
                return self._bedrock.invoke_model(model_id=model_id, prompt=prompt, **kwargs)
            except Exception as e:
                logger.warning(f"Bedrock invocation failed: {e}")
                # Try fallback
                try:
                    return self._sagemaker_fallback(prompt)
                except Exception:
                    raise
        # If no Bedrock client, try fallback if configured
        try:
            return self._sagemaker_fallback(prompt)
        except Exception as e:  # pragma: no cover - fallback path
            logger.error(f"No model provider available: {e}")
            raise

    def invoke_nova(self, prompt: str, max_tokens: int = 2048, temperature: float = 0.7, system_prompt: Optional[str] = None) -> str:
        from src.shared.aws_clients.bedrock_client import NOVA_PRO_MODEL
        if getattr(self, "local_mode", False):
            return self._local_response(prompt)
        return self.invoke_model(model_id=NOVA_PRO_MODEL, prompt=prompt, max_tokens=max_tokens, temperature=temperature, system_prompt=system_prompt)

    def invoke_claude(self, prompt: str, max_tokens: int = 2048, temperature: float = 0.7, model_version: str = "nova-pro-v1:0") -> str:
        # Best-effort: delegate to Bedrock if available, otherwise use generic invoke_model
        if self._bedrock is not None:
            return self._bedrock.invoke_claude(prompt=prompt, max_tokens=max_tokens, temperature=temperature, model_version=model_version)
        model_id = model_version if model_version.startswith("us.") or model_version.startswith("ap.") or model_version.startswith("eu.") else f"anthropic.claude-{model_version}"
        return self.invoke_model(model_id=model_id, prompt=prompt, max_tokens=max_tokens, temperature=temperature)

    def invoke_claude_with_image(self, prompt: str, image_base64: str, media_type: str = "image/jpeg", max_tokens: int = 2048, temperature: float = 0.3) -> str:
        if getattr(self, "local_mode", False):
            return self._local_response(prompt, kind="vision")
        if self._bedrock is not None:
            return self._bedrock.invoke_claude_with_image(prompt=prompt, image_base64=image_base64, media_type=media_type, max_tokens=max_tokens, temperature=temperature)
        # No vision support in fallback; attempt to send the prompt only
        logger.warning("Vision call routed to fallback: image will not be processed by fallback provider")
        return self._sagemaker_fallback(prompt)

    def generate_summary(self, text: str, summary_type: str = "brief", max_tokens: int = 1024) -> str:
        if getattr(self, "local_mode", False):
            return self._local_response(text, kind="summary")
        if self._bedrock is not None:
            try:
                return self._bedrock.generate_summary(text=text, summary_type=summary_type, max_tokens=max_tokens)
            except Exception:
                logger.warning("Bedrock generate_summary failed, falling back")
        prompt = {
            "brief": f"Provide a concise summary (3-5 sentences) of:\n\n{text}",
            "detailed": f"Provide a detailed summary preserving key technical details:\n\n{text}",
            "hierarchical": f"Provide a hierarchical summary with main points and sub-points:\n\n{text}",
        }.get(summary_type, text)
        return self.invoke_nova(prompt, max_tokens=max_tokens, temperature=0.4)
