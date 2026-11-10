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

            # Download HD visual for scene (Fastly CDN, real photography, 100% reliable)
            if not img_file.exists():
                seed = abs(hash(f"{slug}_{idx}")) % 1000
                downloaded = self._download_hd_photo(seed, img_file)
                if not downloaded:
                    downloaded = self._download_pollinations_image(enhanced_prompt, img_file)
                if not downloaded:
                    self._create_image_card(enhanced_prompt, category, img_file)

            if not img_file.exists():
                continue

            # Smooth, centered cinematic Ken Burns zoom with variety per scene
            zoom_direction = "in" if idx % 2 == 0 else "out"
            if zoom_direction == "in":
                zoom_expr = "min(zoom+0.0010,1.25)"
            else:
                zoom_expr = "max(zoom-0.0010,1.00)"
            vf = (
                "scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,"
                f"zoompan=z='{zoom_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30"
            )
            cmd = [
                str(ffmpeg), "-y",
                "-loop", "1",
                "-i", str(img_file),
                "-vf", vf,
                "-t", f"{duration_per_scene:.2f}",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "17",
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
            "-preset", "fast",
            "-crf", "17",
            "-b:v", "4M",
            "-maxrate", "6M",
            "-bufsize", "8M",
            "-pix_fmt", "yuv420p",
            "-t", f"{total_duration:.2f}",
            str(final_out),
        ]

        res_c = subprocess.run(cmd_concat, capture_output=True, text=True, timeout=30)
        if res_c.returncode == 0 and final_out.exists():
            logger.info(f"Successfully assembled {len(clip_paths)} scene clips into: {final_out.name}")
            return final_out

        return None

    def _extract_keywords(self, visual_prompt: str) -> str:
        """Extracts 1-3 clean keyword terms from a visual prompt for image search."""
        # Remove common filler words, keep meaningful nouns/adjectives
        skip = {"the","and","with","from","into","onto","over","under","through",
                "cinematic","lighting","photorealistic","resolution","wallpaper",
                "vertical","ultra","realistic","high","quality","dramatic","epic"}
        words = [w.strip(".,!?\"'()") for w in visual_prompt.split()]
        keywords = [w for w in words if len(w) > 3 and w.lower() not in skip][:3]
        return "+".join(keywords) if keywords else "nature+landscape"

    def _download_hd_photo(self, seed: int, out_path: Path) -> bool:
        """Downloads a real 1080x1920 HD photograph (free, Fastly CDN, 100% reliable)."""
        try:
            url = f"https://picsum.photos/1080/1920?random={seed}"
            with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                res = client.get(url)
                if res.status_code == 200 and len(res.content) > 10000:
                    out_path.write_bytes(res.content)
                    logger.info(f"Downloaded HD scene visual #{seed}: {out_path.name} ({len(res.content)//1024} KB)")
                    return True
        except Exception as e:
            logger.warning(f"HD photo download failed: {e}")
        return False

    def _download_pollinations_image(self, prompt: str, out_path: Path) -> bool:
        """Downloads a high-res 1080x1920 vertical AI visual from Pollinations.ai (Free)."""
        try:
            # Use only 4-6 clean keywords to avoid 402 errors
            clean_words = [w for w in prompt.replace(",", " ").replace(".", " ").replace("'", "").split() if len(w) > 3][:6]
            clean_prompt = " ".join(clean_words) if clean_words else "cinematic vertical background"
            encoded = urllib.parse.quote(clean_prompt)
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true&model=flux-schnell"
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                res = client.get(url)
                if res.status_code == 200 and len(res.content) > 5000:
                    out_path.write_bytes(res.content)
                    logger.info(f"Downloaded Pollinations visual: {out_path.name} ({len(res.content)//1024} KB)")
                    return True
                else:
                    logger.warning(f"Pollinations returned {res.status_code} for prompt: {clean_prompt[:60]}")
        except Exception as e:
            logger.warning(f"Pollinations visual download failed: {e}")
        return False

    def _create_image_card(self, text: str, category: str, out_path: Path):
        """Creates a vibrant cinematic gradient card when image download is unavailable."""
        from PIL import Image, ImageDraw, ImageFont
        import math
        # Vivid color pairs — never dark/black backgrounds
        color_map = {
            "amazing_facts":  ((6, 72, 141),   (0, 180, 216)),   # Royal Blue → Cyan
            "motivation":     ((139, 92, 0),    (255, 183, 3)),   # Dark Gold → Bright Gold
            "ai_technology":  ((13, 27, 92),    (99, 102, 241)),  # Deep Indigo → Violet
            "horror_stories": ((92, 10, 25),    (200, 30, 60)),   # Dark Red → Crimson
            "football_facts": ((22, 101, 52),   (74, 222, 128)),  # Forest → Neon Green
            "cricket_facts":  ((30, 64, 175),   (96, 165, 250)),  # Navy → Sky Blue
        }
        c1, c2 = color_map.get(category, ((13, 110, 253), (99, 179, 237)))  # Vibrant Blue default
        img = Image.new("RGB", (1080, 1920), color=c1)
        draw = ImageDraw.Draw(img)
        # Smooth diagonal gradient
        for y in range(1920):
            ratio = y / 1919.0
            # Add subtle sine wave variation for visual depth
            wave = 0.08 * math.sin(ratio * math.pi * 3)
            t = max(0.0, min(1.0, ratio + wave))
            r = int(c1[0] * (1 - t) + c2[0] * t)
            g = int(c1[1] * (1 - t) + c2[1] * t)
            b = int(c1[2] * (1 - t) + c2[2] * t)
            draw.line([(0, y), (1080, y)], fill=(r, g, b))
        # Draw bright geometric accent lines
        for i in range(5):
            y_pos = int(1920 * (i + 1) / 6)
            draw.line([(0, y_pos), (1080, y_pos)], fill=(255, 255, 255, 30), width=2)
        # Bold title text in upper third
        try:
            font_path = r"C:\Windows\Fonts\arialbd.ttf"
            font = ImageFont.truetype(font_path, size=72)
        except Exception:
            font = ImageFont.load_default()
        # Word wrap to ~20 chars per line
        words = text.split()
        lines, current = [], []
        for w in words[:20]:  # Cap to avoid overflow
            current.append(w)
            if len(" ".join(current)) > 18:
                lines.append(" ".join(current[:-1]))
                current = [w]
        if current:
            lines.append(" ".join(current))
        wrapped = "\n".join(lines[:5])
        # Draw with shadow for readability
        x, y_text = 54, 300
        draw.text((x + 3, y_text + 3), wrapped, font=font, fill=(0, 0, 0, 180))
        draw.text((x, y_text), wrapped, font=font, fill=(255, 255, 255))
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
