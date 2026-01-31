"""Amazon Bedrock client for generative AI."""

import json
import logging
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class BedrockClient:
    """Client for Amazon Bedrock operations."""

    def __init__(self, region: Optional[str] = None) -> None:
        """
        Initialize Bedrock client.

        Args:
            region: AWS region (optional)
        """
        self.region = region or "us-east-1"
        self.client = boto3.client("bedrock-runtime", region_name=self.region)
        logger.info(f"Initialized BedrockClient in region: {self.region}")

    def invoke_model(
        self,
        model_id: str,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs: Any,
    ) -> str:
        """
        Invoke a Bedrock model for text generation.

        Args:
            model_id: Bedrock model identifier
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            **kwargs: Additional model-specific parameters

        Returns:
            Generated text response

        Raises:
            ClientError: If invocation fails
        """
        try:
            # Prepare request body based on model family
            if "anthropic" in model_id.lower():
                body = {
                    "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                    "max_tokens_to_sample": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                }
            elif "ai21" in model_id.lower():
                body = {
                    "prompt": prompt,
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                    "topP": top_p,
                }
            else:  # Amazon Titan or other models
                body = {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": max_tokens,
                        "temperature": temperature,
                        "topP": top_p,
                    },
                }

            # Add any additional parameters
            body.update(kwargs)

            response = self.client.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )

            response_body = json.loads(response["body"].read())

            # Extract text based on model family
            if "anthropic" in model_id.lower():
                text = response_body.get("completion", "")
            elif "ai21" in model_id.lower():
                completions = response_body.get("completions", [])
                text = completions[0].get("data", {}).get("text", "") if completions else ""
            else:  # Amazon Titan
                results = response_body.get("results", [])
                text = results[0].get("outputText", "") if results else ""

            logger.info(f"Successfully invoked model {model_id}")
            return text.strip()

        except ClientError as e:
            logger.error(f"Failed to invoke Bedrock model: {e}")
            raise

    def invoke_claude(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        model_version: str = "3-5-sonnet-20240620-v1:0",
    ) -> str:
        """
        Convenience method to invoke Claude models.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            model_version: Claude model version (3-5-sonnet-20240620-v1:0, 3-sonnet-20240229-v1:0)

        Returns:
            Generated text response
        """
        model_id = f"anthropic.claude-{model_version}"
        return self.invoke_model(
            model_id=model_id,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def invoke_titan(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """
        Convenience method to invoke Amazon Titan models.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text response
        """
        model_id = "amazon.titan-text-premier-v1:0"
        return self.invoke_model(
            model_id=model_id,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def generate_summary(
        self,
        text: str,
        summary_type: str = "brief",
        max_tokens: int = 1024,
    ) -> str:
        """
        Generate a summary of the given text.

        Args:
            text: Text to summarize
            summary_type: Type of summary (brief, detailed, hierarchical)
            max_tokens: Maximum tokens for summary

        Returns:
            Generated summary
        """
        if summary_type == "hierarchical":
            prompt = f"""Please create a hierarchical summary of the following text with main points and sub-points:

{text}

Format the summary with clear hierarchy using bullet points and indentation."""
        elif summary_type == "detailed":
            prompt = f"""Please create a detailed summary of the following text, preserving important details and technical terms:

{text}"""
        else:  # brief
            prompt = f"""Please create a brief, concise summary of the following text:

{text}"""

        return self.invoke_claude(prompt=prompt, max_tokens=max_tokens, temperature=0.5)

    def explain_code(
        self,
        code: str,
        language: str,
        include_line_by_line: bool = True,
    ) -> str:
        """
        Generate an explanation of code.

        Args:
            code: Code to explain
            language: Programming language
            include_line_by_line: Whether to include line-by-line analysis

        Returns:
            Code explanation
        """
        analysis_type = "line-by-line analysis" if include_line_by_line else "overview"
        prompt = f"""Please provide a {analysis_type} explanation of the following {language} code:

```{language}
{code}
```

Include:
1. Overall purpose and functionality
2. {"Line-by-line breakdown" if include_line_by_line else "Key components"}
3. Important concepts and patterns used
4. Potential improvements or issues"""

        return self.invoke_claude(prompt=prompt, max_tokens=2048, temperature=0.3)
