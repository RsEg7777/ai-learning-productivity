"""Amazon Bedrock client — production-grade, no fallbacks."""

import json
import logging
import os
from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# Model IDs — configurable via env, defaults to Nova Pro
NOVA_PRO_MODEL = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
NOVA_LITE_MODEL = os.getenv("BEDROCK_LITE_MODEL_ID", "amazon.nova-lite-v1:0")
# For vision tasks use Claude Sonnet 3.5 v2 (multimodal)
VISION_MODEL = os.getenv("BEDROCK_VISION_MODEL_ID", "us.anthropic.claude-3-5-sonnet-20241022-v2:0")

# If the deployment sets ONLY_AWS_OUTPUTS=true we enforce that
# model IDs are Bedrock-compatible to guarantee outputs come from AWS.
ONLY_AWS_OUTPUTS = os.getenv("ONLY_AWS_OUTPUTS", "false").lower() in ("1", "true", "yes")
if ONLY_AWS_OUTPUTS:
    def _looks_like_bedrock_model(mid: str) -> bool:
        if not mid:
            return False
        m = mid.lower()
        return any(k in m for k in ("amazon.", "us.amazon", "anthropic", "us.anthropic", "nova", "titan"))

    if not (_looks_like_bedrock_model(NOVA_PRO_MODEL) or _looks_like_bedrock_model(NOVA_LITE_MODEL) or _looks_like_bedrock_model(VISION_MODEL)):
        raise RuntimeError(
            "ONLY_AWS_OUTPUTS is set but no Bedrock-compatible model ids found. "
            "Set BEDROCK_MODEL_ID, BEDROCK_LITE_MODEL_ID or BEDROCK_VISION_MODEL_ID to a Bedrock model id."
        )


class BedrockClient:
    """Production Amazon Bedrock client — always calls real AWS."""

    def __init__(self, region: Optional[str] = None) -> None:
        self.region = region or os.getenv("AWS_REGION", "ap-south-1")
        self.client = boto3.client("bedrock-runtime", region_name=self.region)
        logger.info(f"BedrockClient initialised → region={self.region}, model={NOVA_PRO_MODEL}")

    # ──────────────────────────────────────────────────────────────────────────
    # Core invocation
    # ──────────────────────────────────────────────────────────────────────────

    def invoke_model(
        self,
        model_id: str,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Invoke a Bedrock model and return the generated text."""
        try:
            body: dict

            if "nova" in model_id.lower() or "amazon" in model_id.lower() and "nova" in model_id.lower():
                messages = [{"role": "user", "content": [{"text": prompt}]}]
                body = {
                    "messages": messages,
                    "inferenceConfig": {
                        "max_new_tokens": max_tokens,
                        "temperature": temperature,
                        "top_p": top_p,
                    },
                }
                if system_prompt:
                    body["system"] = [{"text": system_prompt}]

            elif "anthropic" in model_id.lower():
                messages = [{"role": "user", "content": prompt}]
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "messages": messages,
                }
                if system_prompt:
                    body["system"] = system_prompt

            elif "titan" in model_id.lower():
                body = {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": max_tokens,
                        "temperature": temperature,
                        "topP": top_p,
                    },
                }
            else:
                # Generic Converse API fallback for other models
                body = {
                    "messages": [{"role": "user", "content": [{"text": prompt}]}],
                    "inferenceConfig": {
                        "maxTokens": max_tokens,
                        "temperature": temperature,
                        "topP": top_p,
                    },
                }

            response = self.client.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            response_body = json.loads(response["body"].read())
            text = self._extract_text(model_id, response_body)
            logger.debug(f"Bedrock {model_id} → {len(text)} chars")
            return text

        except ClientError as e:
            code = e.response["Error"]["Code"]
            msg = e.response["Error"]["Message"]
            logger.error(f"Bedrock ClientError {code}: {msg}")
            if code == "AccessDeniedException":
                raise ValueError(f"Bedrock access denied — check IAM permissions. Model: {model_id}")
            if code == "ResourceNotFoundException":
                raise ValueError(f"Bedrock model not found: {model_id}. Check model ID and region.")
            if code == "ThrottlingException":
                raise ValueError("Bedrock rate limit hit — retry later.")
            if code == "ValidationException":
                raise ValueError(f"Bedrock validation error: {msg}")
            raise ValueError(f"Bedrock error ({code}): {msg}")

        except Exception as e:
            logger.error(f"Bedrock unexpected error: {e}", exc_info=True)
            raise ValueError(f"Bedrock invocation failed: {str(e)}")

    def _extract_text(self, model_id: str, body: dict) -> str:
        """Extract text from Bedrock response based on model family."""
        if "nova" in model_id.lower():
            # Amazon Nova response format
            output = body.get("output", {})
            message = output.get("message", {})
            content = message.get("content", [])
            text = content[0].get("text", "") if content else ""

        elif "anthropic" in model_id.lower():
            content = body.get("content", [])
            text = content[0].get("text", "") if content else body.get("completion", "")

        elif "titan" in model_id.lower():
            results = body.get("results", [])
            text = results[0].get("outputText", "") if results else ""

        else:
            # Try common response shapes
            output = body.get("output", {})
            if output:
                message = output.get("message", {})
                content = message.get("content", [])
                text = content[0].get("text", "") if content else str(output)
            else:
                text = str(body)

        if not text:
            raise ValueError(f"Empty response from model {model_id}. Body: {body}")
        return text.strip()

    # ──────────────────────────────────────────────────────────────────────────
    # Convenience wrappers
    # ──────────────────────────────────────────────────────────────────────────

    def invoke_nova(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Invoke Amazon Nova Pro (primary model)."""
        return self.invoke_model(
            model_id=NOVA_PRO_MODEL,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
        )

    def invoke_claude(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        model_version: str = "nova-pro-v1:0",
    ) -> str:
        """Backward-compatible wrapper — defaults to Nova Pro."""
        if "nova" in model_version:
            model_id = f"amazon.{model_version}"
        elif model_version.startswith("us.") or model_version.startswith("ap.") or model_version.startswith("eu."):
            model_id = model_version
        else:
            model_id = f"anthropic.claude-{model_version}"
        return self.invoke_model(model_id=model_id, prompt=prompt,
                                  max_tokens=max_tokens, temperature=temperature)

    def invoke_claude_with_image(
        self,
        prompt: str,
        image_base64: str,
        media_type: str = "image/jpeg",
        max_tokens: int = 2048,
        temperature: float = 0.3,
    ) -> str:
        """Invoke Claude Sonnet with vision for image understanding tasks."""
        try:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_base64,
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            }

            response = self.client.invoke_model(
                modelId=VISION_MODEL,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            response_body = json.loads(response["body"].read())
            content = response_body.get("content", [])
            text = content[0].get("text", "") if content else ""
            if not text:
                raise ValueError("Empty vision response")
            return text.strip()

        except ClientError as e:
            code = e.response["Error"]["Code"]
            msg = e.response["Error"]["Message"]
            logger.error(f"Vision model error {code}: {msg}")
            raise ValueError(f"Vision processing failed ({code}): {msg}")

    def generate_summary(self, text: str, summary_type: str = "brief", max_tokens: int = 1024) -> str:
        prompts = {
            "brief": f"Provide a concise summary (3-5 sentences) of:\n\n{text}",
            "detailed": f"Provide a detailed summary preserving key technical details:\n\n{text}",
            "hierarchical": f"Provide a hierarchical summary with main points and sub-points:\n\n{text}",
        }
        return self.invoke_nova(prompts.get(summary_type, prompts["brief"]), max_tokens=max_tokens, temperature=0.4)
