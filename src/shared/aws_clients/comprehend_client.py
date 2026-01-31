"""Amazon Comprehend client for natural language processing."""

import logging
from typing import Optional, List, Dict, Any
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class ComprehendClient:
    """Client for Amazon Comprehend operations."""

    def __init__(self, region: Optional[str] = None) -> None:
        """
        Initialize Comprehend client.

        Args:
            region: AWS region (optional)
        """
        self.region = region or "us-east-1"
        self.client = boto3.client("comprehend", region_name=self.region)
        logger.info(f"Initialized ComprehendClient in region: {self.region}")

    def detect_dominant_language(self, text: str) -> Dict[str, Any]:
        """
        Detect the dominant language in text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with language code and confidence score

        Raises:
            ClientError: If detection fails
        """
        try:
            response = self.client.detect_dominant_language(Text=text)
            languages = response.get("Languages", [])

            if languages:
                dominant = languages[0]
                logger.info(
                    f"Detected language: {dominant['LanguageCode']} "
                    f"(confidence: {dominant['Score']:.2f})"
                )
                return dominant
            else:
                return {"LanguageCode": "en", "Score": 0.0}

        except ClientError as e:
            logger.error(f"Failed to detect language: {e}")
            raise

    def extract_key_phrases(self, text: str, language_code: str = "en") -> List[str]:
        """
        Extract key phrases from text.

        Args:
            text: Text to analyze
            language_code: Language code

        Returns:
            List of key phrases

        Raises:
            ClientError: If extraction fails
        """
        try:
            response = self.client.detect_key_phrases(Text=text, LanguageCode=language_code)
            phrases = [phrase["Text"] for phrase in response.get("KeyPhrases", [])]

            logger.info(f"Extracted {len(phrases)} key phrases")
            return phrases

        except ClientError as e:
            logger.error(f"Failed to extract key phrases: {e}")
            raise

    def detect_entities(self, text: str, language_code: str = "en") -> List[Dict[str, Any]]:
        """
        Detect named entities in text.

        Args:
            text: Text to analyze
            language_code: Language code

        Returns:
            List of detected entities

        Raises:
            ClientError: If detection fails
        """
        try:
            response = self.client.detect_entities(Text=text, LanguageCode=language_code)
            entities = response.get("Entities", [])

            logger.info(f"Detected {len(entities)} entities")
            return entities

        except ClientError as e:
            logger.error(f"Failed to detect entities: {e}")
            raise

    def analyze_sentiment(self, text: str, language_code: str = "en") -> Dict[str, Any]:
        """
        Analyze sentiment of text.

        Args:
            text: Text to analyze
            language_code: Language code

        Returns:
            Dictionary with sentiment and scores

        Raises:
            ClientError: If analysis fails
        """
        try:
            response = self.client.detect_sentiment(Text=text, LanguageCode=language_code)

            sentiment_result = {
                "Sentiment": response.get("Sentiment"),
                "Scores": response.get("SentimentScore", {}),
            }

            logger.info(f"Detected sentiment: {sentiment_result['Sentiment']}")
            return sentiment_result

        except ClientError as e:
            logger.error(f"Failed to analyze sentiment: {e}")
            raise

    def detect_syntax(self, text: str, language_code: str = "en") -> List[Dict[str, Any]]:
        """
        Detect syntax and parts of speech in text.

        Args:
            text: Text to analyze
            language_code: Language code

        Returns:
            List of syntax tokens

        Raises:
            ClientError: If detection fails
        """
        try:
            response = self.client.detect_syntax(Text=text, LanguageCode=language_code)
            tokens = response.get("SyntaxTokens", [])

            logger.info(f"Detected {len(tokens)} syntax tokens")
            return tokens

        except ClientError as e:
            logger.error(f"Failed to detect syntax: {e}")
            raise

    def classify_document(
        self,
        text: str,
        endpoint_arn: str,
    ) -> Dict[str, Any]:
        """
        Classify document using a custom classifier.

        Args:
            text: Text to classify
            endpoint_arn: ARN of custom classification endpoint

        Returns:
            Classification results

        Raises:
            ClientError: If classification fails
        """
        try:
            response = self.client.classify_document(Text=text, EndpointArn=endpoint_arn)

            classes = response.get("Classes", [])
            logger.info(f"Classified document into {len(classes)} classes")
            return response

        except ClientError as e:
            logger.error(f"Failed to classify document: {e}")
            raise

    def extract_technical_terms(self, text: str, language_code: str = "en") -> List[str]:
        """
        Extract technical terms from text using entity detection.

        Args:
            text: Text to analyze
            language_code: Language code

        Returns:
            List of technical terms
        """
        # Extract entities and key phrases
        entities = self.detect_entities(text, language_code)
        key_phrases = self.extract_key_phrases(text, language_code)

        # Filter for technical-looking terms
        technical_terms = set()

        # Add entities that look technical (TITLE, ORGANIZATION, etc.)
        for entity in entities:
            if entity["Type"] in ["TITLE", "ORGANIZATION", "COMMERCIAL_ITEM"]:
                technical_terms.add(entity["Text"])

        # Add key phrases that contain technical indicators
        technical_indicators = ["API", "SDK", "HTTP", "JSON", "XML", "SQL", "AWS"]
        for phrase in key_phrases:
            if any(indicator in phrase.upper() for indicator in technical_indicators):
                technical_terms.add(phrase)

        return list(technical_terms)
