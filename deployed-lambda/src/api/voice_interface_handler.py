"""API handler for voice interface endpoints."""

import json
import logging
import base64
from typing import Dict, Any, Optional

from ..services.voice_interface.voice_interface_service import VoiceInterfaceService
from ..shared.aws_clients.transcribe_client import TranscribeClient
from ..shared.aws_clients.polly_client import PollyClient
from ..shared.utils.errors import ValidationError, ContentProcessingError

logger = logging.getLogger(__name__)


class VoiceInterfaceHandler:
    """Handler for voice interface API endpoints."""

    def __init__(self) -> None:
        """Initialize voice interface handler."""
        transcribe_client = TranscribeClient()
        polly_client = PollyClient()
        self.voice_service = VoiceInterfaceService(
            transcribe_client=transcribe_client,
            polly_client=polly_client,
        )
        logger.info("Initialized VoiceInterfaceHandler")

    def handle_transcribe_audio(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Handle audio transcription request.

        Expected event structure:
        {
            "body": {
                "audio_data": "base64-encoded audio",
                "language": "en-US"
            }
        }

        Args:
            event: API Gateway event
            context: Lambda context

        Returns:
            API Gateway response with transcription
        """
        try:
            body = self._parse_body(event)
            
            audio_data_b64 = body.get("audio_data")
            language = body.get("language", "en-US")

            if not audio_data_b64:
                return self._error_response(
                    400,
                    "MISSING_PARAMETER",
                    "audio_data parameter is required",
                )

            # Decode base64 audio data
            audio_data = base64.b64decode(audio_data_b64)

            logger.info(f"Transcribing audio: language={language}, size={len(audio_data)} bytes")

            # Transcribe audio using process_voice_input
            result = self.voice_service.process_voice_input(
                audio_data=audio_data,
                language_code=language,
            )

            response_data = {
                "text": result.text,
                "confidence": result.confidence,
                "language": result.language,
                "timestamps": [
                    {
                        "start": ts.start,
                        "end": ts.end,
                        "text": ts.text,
                    }
                    for ts in result.timestamps
                ],
            }

            logger.info("Successfully transcribed audio")
            return self._success_response(200, response_data)

        except ValidationError as e:
            logger.warning(f"Validation error: {e.message}")
            return self._error_response(400, e.error_code, e.message, e.details)

        except ContentProcessingError as e:
            logger.error(f"Content processing error: {e.message}")
            return self._error_response(500, e.error_code, e.message, e.details)

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return self._error_response(
                500,
                "INTERNAL_ERROR",
                "An unexpected error occurred during audio transcription",
            )

    def handle_synthesize_speech(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Handle text-to-speech synthesis request.

        Expected event structure:
        {
            "body": {
                "text": "text to synthesize",
                "language": "en-US",
                "voice_id": "Joanna"
            }
        }

        Args:
            event: API Gateway event
            context: Lambda context

        Returns:
            API Gateway response with synthesized audio (base64-encoded)
        """
        try:
            body = self._parse_body(event)
            
            text = body.get("text")
            language = body.get("language", "en-US")
            voice_id = body.get("voice_id")

            if not text:
                return self._error_response(
                    400,
                    "MISSING_PARAMETER",
                    "text parameter is required",
                )

            logger.info(f"Synthesizing speech: language={language}, voice={voice_id}")

            # Synthesize speech using generate_audio_response
            result = self.voice_service.generate_audio_response(
                text=text,
                language_code=language,
                voice_id=voice_id,
            )

            # Encode audio as base64
            audio_b64 = base64.b64encode(result.audio_data).decode("utf-8")

            response_data = {
                "audio_data": audio_b64,
                "format": "mp3",
                "language": result.language_code,
                "voice_id": result.voice_id,
            }

            logger.info("Successfully synthesized speech")
            return self._success_response(200, response_data)

        except ValidationError as e:
            logger.warning(f"Validation error: {e.message}")
            return self._error_response(400, e.error_code, e.message, e.details)

        except ContentProcessingError as e:
            logger.error(f"Content processing error: {e.message}")
            return self._error_response(500, e.error_code, e.message, e.details)

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return self._error_response(
                500,
                "INTERNAL_ERROR",
                "An unexpected error occurred during speech synthesis",
            )

    def _parse_body(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Parse request body from event."""
        body = event.get("body", "{}")
        if isinstance(body, str):
            return json.loads(body)
        return body

    def _success_response(self, status_code: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create success API response."""
        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
                "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            },
            "body": json.dumps(data),
        }

    def _error_response(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create error API response."""
        error_data = {
            "error": error_code,
            "message": message,
        }
        if details:
            error_data["details"] = details

        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
                "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            },
            "body": json.dumps(error_data),
        }


# Lambda handler functions
def transcribe_audio_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for audio transcription."""
    handler = VoiceInterfaceHandler()
    return handler.handle_transcribe_audio(event, context)


def synthesize_speech_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for speech synthesis."""
    handler = VoiceInterfaceHandler()
    return handler.handle_synthesize_speech(event, context)
