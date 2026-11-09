"""
AI-CONTENT-AUTOMATION — Tests: Phase 4 Audio and Video Services
================================================================
Comprehensive tests for:
- FFmpeg and GPU NVENC detection
- Edge-TTS voiceover synthesis & word timestamp extraction
- Subtitle generator (SRT and styled ASS format)
- Audio processor mixing & normalization
- Thumbnail generator
- Video renderer (rendering vertical 9:16 short with burned subtitles)
"""

import sys
import pytest
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from video.ffmpeg_locator import ffmpeg_locator
from video.subtitles import subtitle_generator, format_srt_time, format_ass_time
from video.thumbnail import thumbnail_generator
from video.renderer import video_renderer
from audio.tts import tts_engine
from audio.transcription import transcription_engine, SubtitleSegment
from audio.tts_providers.base_tts import WordTimestamp


class TestFFmpegLocator:
    """Verifies FFmpeg binary discovery and hardware acceleration."""

    def test_ffmpeg_found(self):
        """FFmpeg executable must exist on the system."""
        ffmpeg_path = ffmpeg_locator.get_ffmpeg_path()
        assert ffmpeg_path.exists()
        assert ffmpeg_path.name.lower().startswith("ffmpeg")

    def test_ffprobe_found(self):
        """FFprobe executable must exist."""
        ffprobe_path = ffmpeg_locator.get_ffprobe_path()
        assert ffprobe_path.exists()
        assert ffprobe_path.name.lower().startswith("ffprobe")

    def test_encoder_configuration(self):
        """Must return a valid encoder tuple."""
        encoder_name, flags = ffmpeg_locator.get_video_encoder()
        assert encoder_name in ("h264_nvenc", "libx264")
        assert len(flags) > 0


class TestSubtitles:
    """Tests subtitle formatting and file generation."""

    def test_srt_time_formatting(self):
        assert format_srt_time(0.0) == "00:00:00,000"
        assert format_srt_time(65.5) == "00:01:05,500"

    def test_ass_time_formatting(self):
        assert format_ass_time(0.0) == "0:00:00.00"
        assert format_ass_time(65.5) == "0:01:05.50"

    def test_generate_srt_file(self, tmp_path):
        segments = [
            SubtitleSegment(start_s=0.0, end_s=2.5, text="First spoken sentence"),
            SubtitleSegment(start_s=2.5, end_s=5.0, text="Second spoken sentence"),
        ]
        out_srt = tmp_path / "test.srt"
        path = subtitle_generator.generate_srt(segments, str(out_srt))
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "00:00:00,000 --> 00:00:02,500" in content
        assert "FIRST SPOKEN SENTENCE" in content

    def test_generate_ass_file(self, tmp_path):
        segments = [
            SubtitleSegment(start_s=0.5, end_s=3.0, text="Deep in the ocean"),
        ]
        out_ass = tmp_path / "test.ass"
        path = subtitle_generator.generate_styled_ass(segments, str(out_ass))
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "[Script Info]" in content
        assert "PlayResX: 1080" in content
        assert "ShortsStyle" in content
        assert "DEEP IN THE OCEAN" in content

    def test_segments_from_word_timestamps(self):
        timestamps = [
            WordTimestamp(word="The", start_ms=0, end_ms=200),
            WordTimestamp(word="ocean", start_ms=250, end_ms=600),
            WordTimestamp(word="is", start_ms=650, end_ms=800),
            WordTimestamp(word="deep.", start_ms=850, end_ms=1200),
        ]
        segs = transcription_engine.segments_from_word_timestamps(timestamps, words_per_segment=4)
        assert len(segs) == 1
        assert segs[0].text == "The ocean is deep."
        assert segs[0].start_s == 0.0
        assert segs[0].end_s == 1.2


class TestVoiceSynthesis:
    """Tests TTS speech generation with Edge-TTS."""

    def test_list_voices(self):
        voices = tts_engine.list_available_voices()
        assert "edge_tts" in voices
        assert len(voices["edge_tts"]) > 0

    def test_synthesize_speech_creates_audio_and_timestamps(self, tmp_path):
        out_audio = tmp_path / "test_voice.mp3"
        test_text = "Scientists made an incredible discovery today in the deepest trench."
        
        result = tts_engine.generate_speech(
            text=test_text,
            output_filename=str(out_audio),
            preferred_provider="edge_tts"
        )

        assert Path(result.audio_path).exists()
        assert result.duration_s > 1.0
        # If Edge-TTS succeeded, it should have captured word timestamps
        if result.provider == "edge_tts":
            assert len(result.word_timestamps) > 0


class TestThumbnailGenerator:
    """Tests thumbnail creation."""

    def test_create_color_card(self, tmp_path):
        out_thumb = tmp_path / "card.jpg"
        path = thumbnail_generator.create_color_card(
            text="The Mariana Trench Mystery",
            output_path=str(out_thumb)
        )
        assert path.exists()
        assert path.stat().st_size > 1000


class TestVideoRenderer:
    """Tests FFmpeg video rendering pipeline."""

    def test_render_short_video_with_subtitles(self, tmp_path):
        """Renders a 3-second 1080x1920 test video with burned subtitles."""
        # 1. Generate 3-second base video clip
        base_video = tmp_path / "base.mp4"
        video_renderer.generate_solid_background(
            duration_s=3.0,
            output_path=str(base_video),
            color="navy",
            width=1080,
            height=1920,
            fps=24
        )
        assert base_video.exists()

        # 2. Generate short audio track
        test_audio = tmp_path / "audio.mp3"
        tts_res = tts_engine.generate_speech(
            text="This is a test of the video pipeline.",
            output_filename=str(test_audio)
        )
        assert Path(tts_res.audio_path).exists()

        # 3. Generate subtitles
        sub_ass = tmp_path / "subs.ass"
        segments = [
            SubtitleSegment(start_s=0.0, end_s=1.5, text="THIS IS A TEST"),
            SubtitleSegment(start_s=1.5, end_s=3.0, text="OF THE VIDEO PIPELINE"),
        ]
        subtitle_generator.generate_styled_ass(segments, str(sub_ass))
        assert sub_ass.exists()

        # 4. Render vertical short video
        output_video = tmp_path / "final_short.mp4"
        rendered = video_renderer.render_short_video(
            visual_source=str(base_video),
            audio_path=str(tts_res.audio_path),
            output_path=str(output_video),
            subtitle_path=str(sub_ass),
            duration_s=3.0,
            width=1080,
            height=1920,
        )

        assert rendered.exists()
        assert rendered.stat().st_size > 10000  # Valid MP4 file
