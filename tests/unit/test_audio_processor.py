"""Unit tests for audio processor."""

import pytest

from src.services.voice_interface import AudioProcessor


class TestAudioProcessor:
    """Test suite for AudioProcessor."""

    @pytest.fixture
    def audio_processor(self):
        """Create AudioProcessor instance."""
        return AudioProcessor()

    @pytest.fixture
    def sample_audio_data(self):
        """Create sample audio data."""
        return b"fake audio data for testing" * 100  # Make it larger

    def test_initialization(self):
        """Test AudioProcessor initialization."""
        processor = AudioProcessor()
        assert processor is not None

    def test_enhance_audio_with_both_enhancements(
        self,
        audio_processor,
        sample_audio_data,
    ):
        """Test audio enhancement with both noise reduction and quality enhancement."""
        processed_audio, metadata = audio_processor.enhance_audio(
            audio_data=sample_audio_data,
            audio_format="mp3",
            enable_noise_reduction=True,
            enable_quality_enhancement=True,
        )

        assert processed_audio is not None
        assert metadata["noise_reduction_applied"] is True
        assert metadata["quality_enhancement_applied"] is True
        assert metadata["original_size"] == len(sample_audio_data)
        assert metadata["processed_size"] == len(processed_audio)

    def test_enhance_audio_noise_reduction_only(
        self,
        audio_processor,
        sample_audio_data,
    ):
        """Test audio enhancement with noise reduction only."""
        processed_audio, metadata = audio_processor.enhance_audio(
            audio_data=sample_audio_data,
            audio_format="mp3",
            enable_noise_reduction=True,
            enable_quality_enhancement=False,
        )

        assert processed_audio is not None
        assert metadata["noise_reduction_applied"] is True
        assert metadata["quality_enhancement_applied"] is False

    def test_enhance_audio_quality_enhancement_only(
        self,
        audio_processor,
        sample_audio_data,
    ):
        """Test audio enhancement with quality enhancement only."""
        processed_audio, metadata = audio_processor.enhance_audio(
            audio_data=sample_audio_data,
            audio_format="mp3",
            enable_noise_reduction=False,
            enable_quality_enhancement=True,
        )

        assert processed_audio is not None
        assert metadata["noise_reduction_applied"] is False
        assert metadata["quality_enhancement_applied"] is True

    def test_enhance_audio_no_enhancements(
        self,
        audio_processor,
        sample_audio_data,
    ):
        """Test audio enhancement with no enhancements."""
        processed_audio, metadata = audio_processor.enhance_audio(
            audio_data=sample_audio_data,
            audio_format="mp3",
            enable_noise_reduction=False,
            enable_quality_enhancement=False,
        )

        assert processed_audio is not None
        assert metadata["noise_reduction_applied"] is False
        assert metadata["quality_enhancement_applied"] is False

    def test_assess_audio_quality_good(self, audio_processor):
        """Test audio quality assessment for good quality audio."""
        # Large audio file (> 50KB)
        large_audio = b"x" * 60000

        assessment = audio_processor.assess_audio_quality(
            audio_data=large_audio,
            audio_format="mp3",
        )

        assert assessment["quality"] == "good"
        assert assessment["size_kb"] > 50
        assert len(assessment["recommendations"]) == 0

    def test_assess_audio_quality_fair(self, audio_processor):
        """Test audio quality assessment for fair quality audio."""
        # Medium audio file (10-50KB)
        medium_audio = b"x" * 30000

        assessment = audio_processor.assess_audio_quality(
            audio_data=medium_audio,
            audio_format="mp3",
        )

        assert assessment["quality"] == "fair"
        assert 10 < assessment["size_kb"] < 50
        assert len(assessment["recommendations"]) > 0

    def test_assess_audio_quality_poor(self, audio_processor):
        """Test audio quality assessment for poor quality audio."""
        # Small audio file (< 10KB)
        small_audio = b"x" * 5000

        assessment = audio_processor.assess_audio_quality(
            audio_data=small_audio,
            audio_format="mp3",
        )

        assert assessment["quality"] == "poor"
        assert assessment["size_kb"] < 10
        assert len(assessment["recommendations"]) > 0
        assert any("low quality" in rec.lower() for rec in assessment["recommendations"])

    def test_normalize_audio(self, audio_processor, sample_audio_data):
        """Test audio normalization."""
        normalized = audio_processor.normalize_audio(
            audio_data=sample_audio_data,
            audio_format="mp3",
        )

        assert normalized is not None
        # Currently returns original audio
        assert normalized == sample_audio_data

    def test_reduce_noise(self, audio_processor, sample_audio_data):
        """Test noise reduction."""
        reduced = audio_processor.reduce_noise(
            audio_data=sample_audio_data,
            audio_format="mp3",
        )

        assert reduced is not None
        # Currently returns original audio
        assert reduced == sample_audio_data

    def test_convert_format(self, audio_processor, sample_audio_data):
        """Test audio format conversion."""
        converted = audio_processor.convert_format(
            audio_data=sample_audio_data,
            from_format="mp3",
            to_format="wav",
        )

        assert converted is not None
        # Currently returns original audio
        assert converted == sample_audio_data
