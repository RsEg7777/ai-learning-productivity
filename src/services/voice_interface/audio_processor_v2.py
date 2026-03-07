"""
Audio processing utilities for voice interface - Production Version.

This module provides real audio enhancement, noise reduction, and format conversion.
Requires: pydub, numpy (optional: noisereduce for advanced noise reduction)

Installation:
    pip install pydub numpy noisereduce

Note: pydub requires ffmpeg to be installed on the system.
"""

import logging
import io
from typing import Tuple, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Try to import audio processing libraries
try:
    from pydub import AudioSegment
    from pydub.effects import normalize, compress_dynamic_range
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logger.warning("pydub not available. Install with: pip install pydub")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("numpy not available. Install with: pip install numpy")

try:
    import noisereduce as nr
    NOISEREDUCE_AVAILABLE = True
except ImportError:
    NOISEREDUCE_AVAILABLE = False
    logger.info("noisereduce not available (optional). Install with: pip install noisereduce")


class AudioProcessorV2:
    """
    Production-ready audio processing for voice interface.
    
    Features:
    - Noise reduction (if noisereduce available)
    - Volume normalization
    - Dynamic range compression
    - Format conversion
    - Quality enhancement
    """

    def __init__(self):
        """Initialize audio processor."""
        self.capabilities = {
            "basic_processing": PYDUB_AVAILABLE,
            "noise_reduction": PYDUB_AVAILABLE and NUMPY_AVAILABLE and NOISEREDUCE_AVAILABLE,
            "advanced_features": PYDUB_AVAILABLE and NUMPY_AVAILABLE,
        }
        logger.info(f"AudioProcessorV2 initialized with capabilities: {self.capabilities}")

    def enhance_audio(
        self,
        audio_data: bytes,
        audio_format: str = "mp3",
        enable_noise_reduction: bool = True,
        enable_quality_enhancement: bool = True,
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Enhance audio quality and reduce noise.

        Args:
            audio_data: Raw audio data
            audio_format: Audio format (mp3, wav, ogg, etc.)
            enable_noise_reduction: Enable noise reduction
            enable_quality_enhancement: Enable quality enhancement

        Returns:
            Tuple of (processed_audio_data, metadata)
        """
        metadata = {
            "noise_reduction_applied": False,
            "quality_enhancement_applied": False,
            "original_size": len(audio_data),
            "format": audio_format,
        }

        if not PYDUB_AVAILABLE:
            metadata["warning"] = "pydub not available. Returning original audio."
            metadata["processed_size"] = len(audio_data)
            return audio_data, metadata

        try:
            # Load audio
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format=audio_format)
            metadata["duration_ms"] = len(audio)
            
            # Apply noise reduction
            if enable_noise_reduction and self.capabilities["noise_reduction"]:
                audio = self._reduce_noise(audio)
                metadata["noise_reduction_applied"] = True
            
            # Apply quality enhancements
            if enable_quality_enhancement:
                audio = normalize(audio)
                audio = compress_dynamic_range(audio, threshold=-20.0, ratio=4.0)
                
                if audio.frame_rate < 16000:
                    audio = audio.set_frame_rate(16000)
                    metadata["sample_rate_boosted"] = True
                
                metadata["quality_enhancement_applied"] = True
            
            # Export processed audio
            output_buffer = io.BytesIO()
            audio.export(output_buffer, format=audio_format)
            processed_audio = output_buffer.getvalue()
            
            metadata["processed_size"] = len(processed_audio)
            logger.info(f"Audio enhancement complete: {metadata}")
            return processed_audio, metadata

        except Exception as e:
            logger.error(f"Error enhancing audio: {e}", exc_info=True)
            metadata["error"] = str(e)
            metadata["processed_size"] = len(audio_data)
            return audio_data, metadata

    def _reduce_noise(self, audio: 'AudioSegment') -> 'AudioSegment':
        """Reduce background noise from audio."""
        if not self.capabilities["noise_reduction"]:
            return audio
        
        try:
            samples = np.array(audio.get_array_of_samples())
            if audio.channels == 2:
                samples = samples.reshape((-1, 2))
            
            reduced = nr.reduce_noise(y=samples, sr=audio.frame_rate, stationary=True, prop_decrease=0.8)
            
            if audio.channels == 2:
                reduced = reduced.flatten()
            
            return audio._spawn(reduced.tobytes())
        except Exception as e:
            logger.warning(f"Noise reduction failed: {e}")
            return audio

    def convert_format(
        self,
        audio_data: bytes,
        input_format: str,
        output_format: str,
        bitrate: str = "128k",
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Convert audio format."""
        if not PYDUB_AVAILABLE:
            return audio_data, {"error": "pydub not available"}

        try:
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format=input_format)
            output_buffer = io.BytesIO()
            audio.export(output_buffer, format=output_format, bitrate=bitrate)
            
            converted_audio = output_buffer.getvalue()
            metadata = {
                "input_format": input_format,
                "output_format": output_format,
                "original_size": len(audio_data),
                "converted_size": len(converted_audio),
            }
            return converted_audio, metadata
        except Exception as e:
            logger.error(f"Error converting audio: {e}")
            return audio_data, {"error": str(e)}
