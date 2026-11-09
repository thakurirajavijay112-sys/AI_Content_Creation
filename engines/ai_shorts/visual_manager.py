"""
AI-CONTENT-AUTOMATION — Visual Sourcing & Cinematic Motion Generator
=====================================================================
Generates high-definition, vertical 9:16 (1080x1920) video backgrounds for Shorts:
1. Multi-Scene AI Visuals: Generates photorealistic cinematic visuals for every scene
   in the script using free AI visual generation, then animates them with Ken Burns
   motion (cinematic zoom/pan) and concatenates them seamlessly.
2. Licensed Stock Footage: Pexels and Pixabay video APIs when API keys are configured.
3. Thematic Animated Motion: Dynamic color-shifting animated gradients for 100% offline fallback.
"""

import subprocess
import hashlib
import urllib.parse
from pathlib import Path
from typing import Optional, List, Any
import httpx

from config import config
from video.ffmpeg_locator import ffmpeg_locator
from core.logger import get_logger

logger = get_logger(__name__)


class VisualManager:
    """Manages visual assets and dynamic video background generation for short videos."""

    def __init__(self):
        self.visuals_dir = Path(__file__).parent.parent.parent / "generated" / "videos" / "shorts" / "visuals"
        self.visuals_dir.mkdir(parents=True, exist_ok=True)

    def get_or_create_multi_scene_visual(
        self,
        scenes: List[Any],
        category: str,
        total_duration: float,
        title_text: str,
    ) -> Path:
        """
        Creates a complete multi-scene video background matching the script:
        - For each scene, downloads/generates a cinematic 1080x1920 visual matching
          the scene's visual prompt.
        - Applies a smooth Ken Burns zoom/pan effect for each scene's duration.
        - Concatenates all scenes into a continuous, cinematic 1080x1920 video.
        - Automatically falls back to stock footage or dynamic animated motion.
        """
        clean_slug = hashlib.md5(f"{category}_{title_text}_{int(total_duration)}".encode()).hexdigest()[:8]
        out_file = self.visuals_dir / f"cinematic_{category}_{clean_slug}.mp4"

        if out_file.exists() and out_file.stat().st_size > 100000:
            return out_file

        # 1. Try Pexels if API key is present
        if config.stock.pexels_configured:
            stock_path = self._try_fetch_pexels_video(title_text, total_duration)
            if stock_path:
                return stock_path

        # 2. Try multi-scene AI visual generation (Free, beautiful, scene-by-scene)
        if scenes:
            multi_scene_path = self._generate_multi_scene_clips(scenes, category, total_duration, clean_slug)
            if multi_scene_path and multi_scene_path.exists():
                return multi_scene_path

        # 3. Fallback: dynamic vibrant animated gradient motion background
        return self.create_thematic_motion_background(
            category=category,
            duration_s=total_duration,
            title_text=title_text,
        )

    def _generate_multi_scene_clips(
        self,
        scenes: List[Any],
        category: str,
        total_duration: float,
        slug: str,
    ) -> Optional[Path]:
        """Generates scene-by-scene Ken Burns animated clips and concatenates them."""
        ffmpeg = ffmpeg_locator.get_ffmpeg_path()
        scene_count = len(scenes)
        if scene_count == 0:
            return None

        # Calculate duration per scene to cover total duration
        duration_per_scene = max(2.5, total_duration / scene_count)
        clip_paths: List[Path] = []

        logger.info(f"Generating cinematic visuals for {scene_count} scenes ({duration_per_scene:.1f}s each)...")

        for idx, scene in enumerate(scenes):
            prompt = getattr(scene, "visual_prompt", "") or getattr(scene, "narration", "")
            if not prompt:
                prompt = f"{category} cinematic 8k ultra realistic"

            enhanced_prompt = f"{prompt}, cinematic lighting, photorealistic, 8k resolution, vertical 9:16 wallpaper"
            img_file = self.visuals_dir / f"scene_{slug}_{idx}.jpg"
            clip_file = self.visuals_dir / f"scene_clip_{slug}_{idx}.mp4"

            # Download visual if not cached
            if not img_file.exists():
                downloaded = self._download_pollinations_image(enhanced_prompt, img_file)
                if not downloaded:
                    # If Pollinations is unavailable, generate a colorful base card
                    self._create_image_card(enhanced_prompt, category, img_file)

            if not img_file.exists():
                continue

            # Smooth, centered cinematic Ken Burns zoom (d=1 ensures continuous smooth frame progression)
            vf = (
                "scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,"
                "zoompan=z='min(zoom+0.0012,1.20)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30"
            )
            cmd = [
                str(ffmpeg), "-y",
                "-loop", "1",
                "-i", str(img_file),
                "-vf", vf,
                "-t", f"{duration_per_scene:.2f}",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "20",
                "-pix_fmt", "yuv420p",
                str(clip_file),
            ]

            res = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
            if res.returncode == 0 and clip_file.exists():
                clip_paths.append(clip_file)
            else:
                logger.warning(f"Failed to render scene {idx} clip: {res.stderr[:200] if res.stderr else 'unknown error'}")

        if not clip_paths:
            return None

        # Concatenate all scene clips with re-encoding to eliminate glitching & frame tearing
        concat_txt = self.visuals_dir / f"concat_{slug}.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for p in clip_paths:
                f.write(f"file '{p.resolve().as_posix()}'\n")

        final_out = self.visuals_dir / f"cinematic_{category}_{slug}.mp4"
        cmd_concat = [
            str(ffmpeg), "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-t", f"{total_duration:.2f}",
            str(final_out),
        ]

        res_c = subprocess.run(cmd_concat, capture_output=True, text=True, timeout=30)
        if res_c.returncode == 0 and final_out.exists():
            logger.info(f"Successfully assembled {len(clip_paths)} scene clips into: {final_out.name}")
            return final_out

        return None

    def _download_pollinations_image(self, prompt: str, out_path: Path) -> bool:
        """Downloads a high-res 1080x1920 vertical AI visual from Pollinations.ai (Free)."""
        try:
            # Clean and simplify prompt to 5-8 salient words to avoid URL errors and timeouts
            clean_words = [w for w in prompt.replace(",", " ").replace(".", " ").replace("'", "").split() if len(w) > 2][:8]
            clean_prompt = " ".join(clean_words) if clean_words else "cinematic vertical 9:16 background"
            encoded = urllib.parse.quote(clean_prompt)
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true"
            with httpx.Client(timeout=25.0, follow_redirects=True) as client:
                res = client.get(url)
                if res.status_code == 200 and len(res.content) > 5000:
                    out_path.write_bytes(res.content)
                    logger.info(f"Downloaded scene visual: {out_path.name} ({len(res.content)//1024} KB)")
                    return True
        except Exception as e:
            logger.warning(f"Pollinations visual download failed: {e}")
        return False

    def _create_image_card(self, text: str, category: str, out_path: Path):
        """Creates a vibrant, colorful abstract graphic when an image download is unavailable."""
        from PIL import Image, ImageDraw
        color_map = {
            "amazing_facts": ((10, 37, 64), (0, 102, 153)),
            "motivation": ((28, 28, 28), (184, 134, 11)),
            "ai_technology": ((10, 25, 47), (0, 180, 216)),
            "horror_stories": ((31, 5, 11), (102, 12, 24)),
            "football_facts": ((6, 45, 22), (27, 153, 139)),
            "cricket_facts": ((14, 42, 71), (43, 112, 201)),
        }
        c1, c2 = color_map.get(category, ((10, 37, 64), (0, 102, 153)))
        img = Image.new("RGB", (1080, 1920), color=c1)
        draw = ImageDraw.Draw(img)
        # Draw smooth vertical cinematic gradient
        for y in range(0, 1920, 2):
            ratio = y / 1920.0
            r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
            g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
            b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
            draw.line([(0, y), (1080, y)], fill=(r, g, b), width=2)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(out_path), "JPEG", quality=95)

    def _try_fetch_pexels_video(self, query: str, duration_s: float) -> Optional[Path]:
        """Queries Pexels Video API for 9:16 vertical footage."""
        try:
            headers = {"Authorization": config.stock.pexels_api_key}
            params = {
                "query": query,
                "orientation": "portrait",
                "size": "medium",
                "per_page": 3,
            }
            with httpx.Client(timeout=10.0) as client:
                res = client.get("https://api.pexels.com/videos/search", headers=headers, params=params)
                if res.status_code == 200:
                    data = res.json()
                    videos = data.get("videos", [])
                    if videos:
                        files = videos[0].get("video_files", [])
                        for f in files:
                            if f.get("width", 0) < f.get("height", 0):  # Vertical
                                link = f.get("link")
                                if link:
                                    out_name = f"pexels_{hashlib.md5(link.encode()).hexdigest()[:10]}.mp4"
                                    out_path = self.visuals_dir / out_name
                                    if not out_path.exists():
                                        dl = client.get(link, timeout=30.0)
                                        out_path.write_bytes(dl.content)
                                    logger.info(f"Downloaded licensed Pexels clip: {out_path.name}")
                                    return out_path
        except Exception as e:
            logger.warning(f"Pexels fetch failed: {e}")
        return None

    def create_thematic_motion_background(
        self,
        category: str,
        duration_s: float,
        title_text: str,
        width: int = 1080,
        height: int = 1920,
    ) -> Path:
        """
        Generates a vibrant, dynamic color-shifting gradient motion background clip via FFmpeg.
        Never pitch black: blends vibrant category colors with dynamic wave motion.
        """
        clean_slug = hashlib.md5(f"{category}_{title_text}_{int(duration_s)}".encode()).hexdigest()[:8]
        out_file = self.visuals_dir / f"motion_{category}_{clean_slug}.mp4"

        if out_file.exists() and out_file.stat().st_size > 50000:
            return out_file

        ffmpeg = ffmpeg_locator.get_ffmpeg_path()

        # Rich, vibrant thematic color pairs (never pitch black)
        color_map = {
            "amazing_facts": ("#0a2540", "#006699"),   # Deep Ocean to Cerulean Blue
            "motivation": ("#1c1c1c", "#b8860b"),      # Charcoal to Dark Goldenrod
            "ai_technology": ("#0a192f", "#00b4d8"),   # Deep Cyber to Glowing Cyan
            "horror_stories": ("#1f050b", "#660c18"),  # Obsidian to Crimson
            "football_facts": ("#062d16", "#1b998b"),  # Dark Turf to Electric Jade
            "cricket_facts": ("#0e2a47", "#2b70c9"),   # Navy to Stadium Blue
        }
        c1, c2 = color_map.get(category, ("#0a2540", "#006699"))

        # Animated wave blend filter that smoothly shifts between the two colors
        filter_str = (
            f"color=c={c1}:s={width}x{height}:r=30:d={duration_s}[c1];"
            f"color=c={c2}:s={width}x{height}:r=30:d={duration_s}[c2];"
            f"[c1][c2]blend=all_expr='A*(0.6+0.4*sin(2*PI*T/8))+B*(0.4-0.4*sin(2*PI*T/8))',"
            f"vignette=PI/5,"
            f"format=yuv420p[out]"
        )

        cmd = [
            str(ffmpeg), "-y",
            "-f", "lavfi",
            "-i", filter_str,
            "-t", str(duration_s),
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            str(out_file),
        ]

        logger.info(f"Generating vibrant motion background for {category} ({duration_s:.1f}s)...")
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
        if res.returncode != 0:
            logger.error(f"FFmpeg motion background failed: {res.stderr}")
            from video.renderer import video_renderer
            return video_renderer.generate_solid_background(duration_s, str(out_file), color="blue")

        return out_file


# Singleton instance
visual_manager = VisualManager()
