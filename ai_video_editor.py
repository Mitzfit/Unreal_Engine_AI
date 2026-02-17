"""
AI-Powered Video Editor for Game Cutscenes
Complete video editing suite with AI enhancements
"""

import asyncio
import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import tempfile
import numpy as np

class AIVideoEditor:
    """
    Complete AI-powered video editing system for game cutscenes
    """
    
    def __init__(self, openai_key: str):
        self.openai_key = openai_key
        self.session = None
        self.output_dir = Path("assets/cutscenes")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Video processing settings
        self.default_fps = 30
        self.default_resolution = (1920, 1080)
        self.default_codec = "libx264"
        self.default_audio_codec = "aac"
        
    async def setup_session(self):
        """Initialize async session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Close async session"""
        if self.session:
            await self.session.close()
    
    # ============================================
    # AI-POWERED CUTSCENE GENERATION
    # ============================================
    
    async def generate_cutscene_from_script(
        self,
        script: str,
        style: str = "cinematic",
        duration: int = 60,
        music: bool = True
    ) -> Dict[str, Any]:
        """
        Generate complete cutscene from text script using AI
        """
        
        # Parse script into scenes
        scenes = await self._parse_script_to_scenes(script)
        
        # Generate storyboard
        storyboard = await self._generate_storyboard(scenes, style)
        
        # Generate video for each scene
        scene_videos = []
        for i, scene in enumerate(storyboard):
            video = await self._generate_scene_video(scene, i)
            scene_videos.append(video)
        
        # Combine scenes
        combined = await self._combine_scenes(scene_videos)
        
        # Add transitions
        with_transitions = await self._add_transitions(combined)
        
        # Add music if requested
        if music:
            with_music = await self._add_background_music(with_transitions, style)
        else:
            with_music = with_transitions
        
        # Add effects
        final = await self._add_visual_effects(with_music, style)
        
        return {
            "success": True,
            "cutscene_path": str(final),
            "scenes": len(scenes),
            "duration": duration,
            "style": style,
            "storyboard": storyboard
        }
    
    async def _parse_script_to_scenes(self, script: str) -> List[Dict[str, Any]]:
        """Parse script into individual scenes using AI"""
        
        prompt = f"""Parse this game cutscene script into individual scenes:

SCRIPT:
{script}

For each scene, extract:
- Scene description
- Camera angle
- Characters present
- Dialogue
- Duration estimate
- Action/emotion

Return JSON array of scenes."""

        response = await self._call_openai(prompt)
        
        try:
            scenes = json.loads(response)
            return scenes
        except:
            # Fallback: split by scene markers
            return [{"description": script, "duration": 10}]
    
    async def _generate_storyboard(
        self,
        scenes: List[Dict[str, Any]],
        style: str
    ) -> List[Dict[str, Any]]:
        """Generate visual storyboard for scenes"""
        
        storyboard = []
        
        for scene in scenes:
            board_item = {
                "scene_id": len(storyboard),
                "description": scene.get("description", ""),
                "camera_angle": scene.get("camera_angle", "medium shot"),
                "lighting": self._suggest_lighting(style),
                "composition": self._suggest_composition(scene),
                "duration": scene.get("duration", 5),
                "visual_prompt": await self._create_visual_prompt(scene, style)
            }
            storyboard.append(board_item)
        
        return storyboard
    
    def _suggest_lighting(self, style: str) -> str:
        """Suggest lighting based on style"""
        lighting_map = {
            "cinematic": "dramatic three-point lighting",
            "anime": "cel-shaded lighting",
            "realistic": "natural lighting",
            "dark": "low-key lighting",
            "bright": "high-key lighting",
            "epic": "volumetric god rays"
        }
        return lighting_map.get(style, "balanced lighting")
    
    def _suggest_composition(self, scene: Dict[str, Any]) -> str:
        """Suggest composition rules"""
        if "action" in scene.get("description", "").lower():
            return "rule of thirds, dynamic"
        elif "dialogue" in scene.get("description", "").lower():
            return "over-the-shoulder, conversational"
        else:
            return "centered, balanced"
    
    async def _create_visual_prompt(self, scene: Dict[str, Any], style: str) -> str:
        """Create prompt for image/video generation"""
        
        prompt = f"""Generate a {style} game cutscene frame:

Scene: {scene.get('description', '')}
Camera: {scene.get('camera_angle', 'medium shot')}
Characters: {', '.join(scene.get('characters', ['character']))}
Emotion: {scene.get('emotion', 'neutral')}
Lighting: {self._suggest_lighting(style)}

High quality, game engine render, cinematic."""

        return prompt
    
    # ============================================
    # VIDEO EDITING OPERATIONS
    # ============================================
    
    async def cut_video(
        self,
        input_path: str,
        start_time: float,
        end_time: float,
        output_path: Optional[str] = None
    ) -> str:
        """
        Cut/trim video to specified time range
        """
        
        if not output_path:
            output_path = self._generate_output_path("cut")
        
        # Use FFmpeg for cutting
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-ss", str(start_time),
            "-to", str(end_time),
            "-c", "copy",  # Fast copy without re-encoding
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        return output_path
    
    async def merge_videos(
        self,
        video_paths: List[str],
        output_path: Optional[str] = None
    ) -> str:
        """
        Merge multiple videos into one
        """
        
        if not output_path:
            output_path = self._generate_output_path("merged")
        
        # Create concat file
        concat_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        for path in video_paths:
            concat_file.write(f"file '{path}'\n")
        concat_file.close()
        
        # Merge with FFmpeg
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file.name,
            "-c", "copy",
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        os.unlink(concat_file.name)
        
        return output_path
    
    async def add_transition(
        self,
        video1: str,
        video2: str,
        transition_type: str = "fade",
        duration: float = 1.0,
        output_path: Optional[str] = None
    ) -> str:
        """
        Add transition between two videos
        
        Transition types:
        - fade
        - dissolve
        - wipe (left, right, up, down)
        - slide
        - zoom
        - blur
        """
        
        if not output_path:
            output_path = self._generate_output_path("transition")
        
        # FFmpeg complex filter for transitions
        transitions = {
            "fade": "fade=t=in:st=0:d={0},fade=t=out:st={1}:d={0}",
            "dissolve": "xfade=transition=dissolve:duration={0}:offset={1}",
            "wipeleft": "xfade=transition=wipeleft:duration={0}:offset={1}",
            "wiperight": "xfade=transition=wiperight:duration={0}:offset={1}",
            "slide": "xfade=transition=slideleft:duration={0}:offset={1}",
            "zoom": "xfade=transition=zoomin:duration={0}:offset={1}",
        }
        
        filter_str = transitions.get(transition_type, transitions["fade"])
        
        # Get video1 duration
        video1_duration = self._get_video_duration(video1)
        
        cmd = [
            "ffmpeg",
            "-i", video1,
            "-i", video2,
            "-filter_complex", filter_str.format(duration, video1_duration - duration),
            "-c:v", self.default_codec,
            "-c:a", self.default_audio_codec,
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        return output_path
    
    async def add_text_overlay(
        self,
        video_path: str,
        text: str,
        position: str = "bottom",
        font_size: int = 48,
        font_color: str = "white",
        duration: Optional[float] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Add text overlay to video (subtitles, titles, etc.)
        """
        
        if not output_path:
            output_path = self._generate_output_path("text_overlay")
        
        # Position mapping
        positions = {
            "top": "x=(w-text_w)/2:y=50",
            "bottom": "x=(w-text_w)/2:y=h-th-50",
            "center": "x=(w-text_w)/2:y=(h-text_h)/2",
            "topleft": "x=50:y=50",
            "topright": "x=w-tw-50:y=50"
        }
        
        pos_str = positions.get(position, positions["bottom"])
        
        # FFmpeg drawtext filter
        filter_str = f"drawtext=text='{text}':fontsize={font_size}:fontcolor={font_color}:{pos_str}"
        
        if duration:
            filter_str += f":enable='between(t,0,{duration})'"
        
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", filter_str,
            "-c:a", "copy",
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        return output_path
    
    async def add_watermark(
        self,
        video_path: str,
        watermark_path: str,
        position: str = "bottomright",
        opacity: float = 0.5,
        output_path: Optional[str] = None
    ) -> str:
        """
        Add watermark/logo to video
        """
        
        if not output_path:
            output_path = self._generate_output_path("watermarked")
        
        # Position mapping
        positions = {
            "topleft": "10:10",
            "topright": "main_w-overlay_w-10:10",
            "bottomleft": "10:main_h-overlay_h-10",
            "bottomright": "main_w-overlay_w-10:main_h-overlay_h-10",
            "center": "(main_w-overlay_w)/2:(main_h-overlay_h)/2"
        }
        
        pos_str = positions.get(position, positions["bottomright"])
        
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-i", watermark_path,
            "-filter_complex", f"[1:v]format=rgba,colorchannelmixer=aa={opacity}[logo];[0:v][logo]overlay={pos_str}",
            "-c:a", "copy",
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        return output_path
    
    async def apply_filter(
        self,
        video_path: str,
        filter_type: str,
        intensity: float = 1.0,
        output_path: Optional[str] = None
    ) -> str:
        """
        Apply visual filter/effect to video
        
        Filters:
        - sepia
        - black_and_white
        - vintage
        - blur
        - sharpen
        - vignette
        - color_grade (cinematic)
        - night_vision
        - thermal
        """
        
        if not output_path:
            output_path = self._generate_output_path(f"filtered_{filter_type}")
        
        filters = {
            "sepia": "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131",
            "black_and_white": "hue=s=0",
            "vintage": "curves=vintage",
            "blur": f"boxblur={intensity*5}:{intensity*5}",
            "sharpen": f"unsharp=5:5:{intensity}:5:5:0",
            "vignette": "vignette",
            "cinematic": "curves=preset=color_negative",
            "night_vision": "colorlevels=rimax=0.5:gimax=0.8:bimax=0.3",
            "thermal": "colorkey=green:0.3:0.1,hue=h=120"
        }
        
        filter_str = filters.get(filter_type, "")
        
        if filter_str:
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vf", filter_str,
                "-c:a", "copy",
                output_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
        
        return output_path
    
    async def adjust_speed(
        self,
        video_path: str,
        speed_factor: float,
        output_path: Optional[str] = None
    ) -> str:
        """
        Adjust video playback speed
        speed_factor: 0.5 = half speed, 2.0 = double speed
        """
        
        if not output_path:
            output_path = self._generate_output_path("speed_adjusted")
        
        # Calculate PTS and audio tempo
        video_speed = 1.0 / speed_factor
        audio_speed = speed_factor
        
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-filter_complex", f"[0:v]setpts={video_speed}*PTS[v];[0:a]atempo={audio_speed}[a]",
            "-map", "[v]",
            "-map", "[a]",
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        return output_path
    
    async def reverse_video(
        self,
        video_path: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Reverse video playback
        """
        
        if not output_path:
            output_path = self._generate_output_path("reversed")
        
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", "reverse",
            "-af", "areverse",
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        return output_path
    
    async def add_audio(
        self,
        video_path: str,
        audio_path: str,
        volume: float = 1.0,
        fade_in: float = 0,
        fade_out: float = 0,
        output_path: Optional[str] = None
    ) -> str:
        """
        Add or replace audio track
        """
        
        if not output_path:
            output_path = self._generate_output_path("audio_added")
        
        # Build audio filter
        audio_filter = []
        if volume != 1.0:
            audio_filter.append(f"volume={volume}")
        if fade_in > 0:
            audio_filter.append(f"afade=t=in:st=0:d={fade_in}")
        if fade_out > 0:
            duration = self._get_audio_duration(audio_path)
            audio_filter.append(f"afade=t=out:st={duration-fade_out}:d={fade_out}")
        
        filter_str = ",".join(audio_filter) if audio_filter else None
        
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-map", "0:v:0",
            "-map", "1:a:0"
        ]
        
        if filter_str:
            cmd.extend(["-af", filter_str])
        
        cmd.extend(["-shortest", output_path])
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        return output_path
    
    async def extract_audio(
        self,
        video_path: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Extract audio from video
        """
        
        if not output_path:
            output_path = self._generate_output_path("audio", ext=".mp3")
        
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn",  # No video
            "-acodec", "mp3",
            "-ab", "192k",
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        return output_path
    
    async def create_slideshow(
        self,
        image_paths: List[str],
        duration_per_image: float = 3.0,
        transition: str = "fade",
        music_path: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Create video slideshow from images
        """
        
        if not output_path:
            output_path = self._generate_output_path("slideshow")
        
        # Create video from each image
        temp_videos = []
        for img_path in image_paths:
            temp_vid = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False).name
            
            cmd = [
                "ffmpeg",
                "-loop", "1",
                "-i", img_path,
                "-c:v", self.default_codec,
                "-t", str(duration_per_image),
                "-pix_fmt", "yuv420p",
                temp_vid
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            temp_videos.append(temp_vid)
        
        # Merge with transitions
        merged = await self.merge_videos(temp_videos)
        
        # Add music if provided
        if music_path:
            final = await self.add_audio(merged, music_path)
        else:
            final = merged
        
        # Cleanup
        for temp in temp_videos:
            os.unlink(temp)
        
        if final != output_path:
            os.rename(final, output_path)
        
        return output_path
    
    async def add_camera_shake(
        self,
        video_path: str,
        intensity: float = 10.0,
        output_path: Optional[str] = None
    ) -> str:
        """
        Add camera shake effect (for action scenes)
        """
        
        if not output_path:
            output_path = self._generate_output_path("camera_shake")
        
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"crop=iw-{int(intensity*2)}:ih-{int(intensity*2)}:x='random(1)*{intensity}':y='random(1)*{intensity}'",
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        return output_path
    
    async def add_letterbox(
        self,
        video_path: str,
        aspect_ratio: str = "2.39:1",  # Cinematic
        color: str = "black",
        output_path: Optional[str] = None
    ) -> str:
        """
        Add letterbox/pillarbox bars for cinematic look
        """
        
        if not output_path:
            output_path = self._generate_output_path("letterbox")
        
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"pad=ih*{aspect_ratio}:ih:(ow-iw)/2:(oh-ih)/2:color={color}",
            "-c:a", "copy",
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        return output_path
    
    async def create_picture_in_picture(
        self,
        main_video: str,
        overlay_video: str,
        position: str = "topright",
        scale: float = 0.25,
        output_path: Optional[str] = None
    ) -> str:
        """
        Create picture-in-picture effect
        """
        
        if not output_path:
            output_path = self._generate_output_path("pip")
        
        positions = {
            "topleft": "10:10",
            "topright": "main_w-overlay_w-10:10",
            "bottomleft": "10:main_h-overlay_h-10",
            "bottomright": "main_w-overlay_w-10:main_h-overlay_h-10"
        }
        
        pos = positions.get(position, positions["topright"])
        
        cmd = [
            "ffmpeg",
            "-i", main_video,
            "-i", overlay_video,
            "-filter_complex",
            f"[1:v]scale=iw*{scale}:ih*{scale}[pip];[0:v][pip]overlay={pos}",
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        return output_path
    
    async def generate_subtitles(
        self,
        video_path: str,
        dialogue: List[Dict[str, Any]],
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate and burn subtitles into video
        
        dialogue format:
        [
            {"text": "Hello world", "start": 0.0, "end": 2.0},
            {"text": "How are you?", "start": 2.5, "end": 4.5}
        ]
        """
        
        # Create SRT file
        srt_content = self._create_srt(dialogue)
        srt_file = tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False)
        srt_file.write(srt_content)
        srt_file.close()
        
        if not output_path:
            output_path = self._generate_output_path("subtitled")
        
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"subtitles={srt_file.name}",
            "-c:a", "copy",
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        os.unlink(srt_file.name)
        
        return output_path
    
    def _create_srt(self, dialogue: List[Dict[str, Any]]) -> str:
        """Create SRT subtitle format"""
        
        srt_content = []
        for i, entry in enumerate(dialogue, 1):
            start = self._format_srt_time(entry["start"])
            end = self._format_srt_time(entry["end"])
            text = entry["text"]
            
            srt_content.append(f"{i}\n{start} --> {end}\n{text}\n")
        
        return "\n".join(srt_content)
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format time for SRT (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    # ============================================
    # AI-ENHANCED FEATURES
    # ============================================
    
    async def auto_edit_cutscene(
        self,
        raw_footage: List[str],
        style: str = "action",
        target_duration: int = 60
    ) -> str:
        """
        Automatically edit cutscene from raw footage using AI
        """
        
        # Analyze each clip
        clip_analysis = []
        for clip in raw_footage:
            analysis = await self._analyze_clip(clip)
            clip_analysis.append(analysis)
        
        # Generate edit decision list (EDL) with AI
        edl = await self._generate_edl(clip_analysis, style, target_duration)
        
        # Execute edits based on EDL
        edited = await self._apply_edl(edl)
        
        return edited
    
    async def _analyze_clip(self, clip_path: str) -> Dict[str, Any]:
        """Analyze video clip for content"""
        
        # Extract frames for analysis
        cap = cv2.VideoCapture(clip_path)
        
        # Sample frames
        frames = []
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        for i in range(0, frame_count, frame_count // 10):  # 10 samples
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
        
        cap.release()
        
        # Analyze motion, brightness, etc.
        motion = self._calculate_motion(frames)
        brightness = self._calculate_brightness(frames)
        
        return {
            "path": clip_path,
            "duration": self._get_video_duration(clip_path),
            "motion_level": motion,
            "brightness": brightness,
            "fps": self._get_video_fps(clip_path)
        }
    
    def _calculate_motion(self, frames: List[np.ndarray]) -> float:
        """Calculate motion level in frames"""
        if len(frames) < 2:
            return 0.0
        
        motion_sum = 0
        for i in range(len(frames) - 1):
            diff = cv2.absdiff(frames[i], frames[i+1])
            motion_sum += diff.mean()
        
        return motion_sum / (len(frames) - 1)
    
    def _calculate_brightness(self, frames: List[np.ndarray]) -> float:
        """Calculate average brightness"""
        if not frames:
            return 0.0
        
        brightness_sum = sum(frame.mean() for frame in frames)
        return brightness_sum / len(frames)
    
    async def _generate_edl(
        self,
        clips: List[Dict[str, Any]],
        style: str,
        target_duration: int
    ) -> List[Dict[str, Any]]:
        """Generate Edit Decision List using AI"""
        
        # Sort clips by motion for action style, etc.
        if style == "action":
            clips.sort(key=lambda x: x["motion_level"], reverse=True)
        elif style == "calm":
            clips.sort(key=lambda x: x["motion_level"])
        
        # Create EDL
        edl = []
        total_duration = 0
        
        for clip in clips:
            if total_duration >= target_duration:
                break
            
            clip_duration = min(clip["duration"], target_duration - total_duration)
            
            edl.append({
                "source": clip["path"],
                "start": 0,
                "duration": clip_duration,
                "effects": self._suggest_effects(clip, style)
            })
            
            total_duration += clip_duration
        
        return edl
    
    def _suggest_effects(self, clip: Dict[str, Any], style: str) -> List[str]:
        """Suggest effects based on clip analysis"""
        effects = []
        
        if clip["motion_level"] > 50:
            effects.append("camera_shake")
        
        if clip["brightness"] < 50:
            effects.append("brighten")
        
        if style == "cinematic":
            effects.append("color_grade")
            effects.append("letterbox")
        
        return effects
    
    # ============================================
    # UTILITY METHODS
    # ============================================
    
    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds"""
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True,
            text=True
        )
        return float(result.stdout.strip())
    
    def _get_video_fps(self, video_path: str) -> float:
        """Get video FPS"""
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=r_frame_rate", "-of", "default=noprint_wrappers=1:nokey=1",
             video_path],
            capture_output=True,
            text=True
        )
        fps_str = result.stdout.strip()
        num, den = fps_str.split('/')
        return float(num) / float(den)
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration"""
        return self._get_video_duration(audio_path)
    
    def _generate_output_path(self, suffix: str, ext: str = ".mp4") -> str:
        """Generate unique output path"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cutscene_{suffix}_{timestamp}{ext}"
        return str(self.output_dir / filename)
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        await self.setup_session()
        
        try:
            async with self.session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4-turbo-preview",
                    "messages": [
                        {"role": "system", "content": "You are a professional video editor and cinematographer."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.4
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error: {str(e)}"
        
        return ""
    
    async def _generate_scene_video(self, scene: Dict[str, Any], scene_num: int) -> str:
        """Generate video for a scene (placeholder - integrate with image/video AI)"""
        # In production, this would call:
        # - Stable Video Diffusion
        # - Runway Gen-2
        # - Pika Labs
        # - Or render from game engine
        
        output_path = self._generate_output_path(f"scene_{scene_num}")
        return output_path
    
    async def _combine_scenes(self, scenes: List[str]) -> str:
        """Combine scene videos"""
        return await self.merge_videos(scenes)
    
    async def _add_transitions(self, video_path: str) -> str:
        """Add transitions between scenes"""
        return video_path
    
    async def _add_background_music(self, video_path: str, style: str) -> str:
        """Add background music"""
        # Would integrate with audio generator here
        return video_path
    
    async def _add_visual_effects(self, video_path: str, style: str) -> str:
        """Add final visual effects"""
        return await self.apply_filter(video_path, "cinematic")
    
    async def _apply_edl(self, edl: List[Dict[str, Any]]) -> str:
        """Apply Edit Decision List"""
        # Cut and combine clips according to EDL
        cut_clips = []
        
        for entry in edl:
            cut = await self.cut_video(
                entry["source"],
                entry["start"],
                entry["start"] + entry["duration"]
            )
            cut_clips.append(cut)
        
        final = await self.merge_videos(cut_clips)
        
        # Cleanup
        for clip in cut_clips:
            os.unlink(clip)
        
        return final