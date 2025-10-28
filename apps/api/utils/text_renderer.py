"""
Text rendering utilities with emoji support
"""
import logging
import re
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from utils.font_manager import find_emoji_font, find_text_font

logger = logging.getLogger(__name__)

# Emoji detection pattern
EMOJI_PATTERN = re.compile(
    "[\U0001F600-\U0001F64F]|"
    "[\U0001F300-\U0001F5FF]|"
    "[\U0001F680-\U0001F6FF]|"
    "[\U0001F700-\U0001F77F]|"
    "[\U0001F780-\U0001F7FF]|"
    "[\U0001F800-\U0001F8FF]|"
    "[\U00002600-\U000027BF]|"
    "[\U0001F900-\U0001F9FF]|"
    "[\U0001FA00-\U0001FA6F]|"
    "[\U0001FA70-\U0001FAFF]|"
    "[\U00002300-\U000023FF]|"
    "[\U00002B00-\U00002BFF]|"
    "[\U00010000-\U0001FFFF]|"
    "[\U0000FE0F]"
)

# Text style presets
TEXT_PRESETS = {
    "clean": {"text_color": (255, 255, 255), "outline_color": (0, 0, 0), "outline_width": 0},
    "bold": {"text_color": (255, 255, 255), "outline_color": (0, 0, 0), "outline_width": 3},
    "subtle": {"text_color": (255, 255, 255), "outline_color": (128, 128, 128), "outline_width": 1},
    "yellow": {"text_color": (255, 255, 0), "outline_color": (0, 0, 0), "outline_width": 2},
    "shadow": {"text_color": (255, 255, 255), "outline_color": (50, 50, 50), "outline_width": 2},
}


def is_emoji(character: str) -> bool:
    """Check if character is an emoji."""
    return bool(EMOJI_PATTERN.match(character))


class EmojiTextRenderer:
    """
    Renderer for text with emoji support.

    Handles mixed text/emoji rendering with customizable styling.
    Uses separate fonts for text and emojis.
    """

    def __init__(
        self,
        font_size: int = 48,
        text_font_path: Optional[str] = None,
        emoji_font_path: Optional[str] = None,
        text_color: tuple[int, int, int] = (255, 255, 255),
        outline_color: tuple[int, int, int] = (0, 0, 0),
        outline_width: int = 2,
        preset: Optional[str] = None,
    ):
        """
        Initialize text renderer.

        Args:
            font_size: Font size in pixels
            text_font_path: Custom path to text font
            emoji_font_path: Custom path to emoji font
            text_color: RGB color for text
            outline_color: RGB color for outline
            outline_width: Outline width in pixels
            preset: Preset name (overrides colors if provided)
        """
        self.font_size = font_size

        # Apply preset if provided
        if preset and preset in TEXT_PRESETS:
            preset_config = TEXT_PRESETS[preset]
            self.text_color = preset_config["text_color"]
            self.outline_color = preset_config["outline_color"]
            self.outline_width = preset_config["outline_width"]
            logger.info(f"Applied text preset: {preset}")
        else:
            self.text_color = text_color
            self.outline_color = outline_color
            self.outline_width = outline_width
            if preset:
                logger.warning(f"Unknown preset '{preset}', using default config")

        # Load fonts
        self.text_font_path = find_text_font(text_font_path)
        self.emoji_font_path = emoji_font_path or find_emoji_font()

        try:
            self.text_font = ImageFont.truetype(self.text_font_path, self.font_size)
            self.emoji_font = ImageFont.truetype(self.emoji_font_path, self.font_size)
            logger.info(
                f"Fonts loaded - Text: {Path(self.text_font_path).name}, "
                f"Emoji: {Path(self.emoji_font_path).name}"
            )
        except Exception as e:
            logger.error(f"Error loading fonts: {str(e)}", exc_info=True)
            self.text_font = ImageFont.load_default()
            self.emoji_font = self.text_font

        # Render cache for performance
        self._render_cache: dict[str, np.ndarray] = {}

    def _split_text_and_emojis(self, text: str) -> list[tuple[str, bool]]:
        """
        Split text into segments of text and emojis.

        Args:
            text: Input text

        Returns:
            List of (segment, is_emoji) tuples
        """
        if not text:
            return []

        segments = []
        current = ""
        current_is_emoji = False
        i = 0

        while i < len(text):
            char = text[i]
            is_em = is_emoji(char)

            if is_em:
                # Handle multi-char emojis (with variation selectors, etc.)
                emoji_end = i + 1
                while emoji_end < len(text) and (
                    text[emoji_end] in '\u200d\ufe0f' or is_emoji(text[emoji_end])
                ):
                    emoji_end += 1

                # Flush current text segment
                if current and not current_is_emoji:
                    segments.append((current, False))
                    current = ""

                # Add emoji segment
                segments.append((text[i:emoji_end], True))
                i = emoji_end
            else:
                # Flush current emoji if switching to text
                if current_is_emoji and current:
                    segments.append((current, True))
                    current = ""

                current += char
                current_is_emoji = False
                i += 1

        # Flush remaining
        if current:
            segments.append((current, current_is_emoji))

        return segments

    def _calc_line_size(self, line: str) -> tuple[int, int]:
        """Calculate rendered size of a line."""
        segments = self._split_text_and_emojis(line)
        width = 0
        height = 0

        for text, is_emoji_seg in segments:
            if not text:
                continue

            font = self.emoji_font if is_emoji_seg else self.text_font
            bbox = font.getbbox(text)
            width += bbox[2] - bbox[0]
            height = max(height, bbox[3] - bbox[1])

        return width, height

    def _hard_wrap_text(self, text: str, max_width: int) -> str:
        """
        Hard wrap text to fit within max width.

        Args:
            text: Input text
            max_width: Maximum line width in pixels

        Returns:
            Wrapped text with newlines
        """
        lines = []
        current = ""

        for word in text.split():
            test = (current + " " + word).strip()
            width, _ = self._calc_line_size(test)

            if width <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word

        if current:
            lines.append(current)

        return "\n".join(lines)

    def render_text(self, text: str, max_width: Optional[int] = None) -> np.ndarray:
        """
        Render text with emoji support.

        Args:
            text: Text to render
            max_width: Maximum width for wrapping (optional)

        Returns:
            BGRA numpy array with rendered text
        """
        # Check cache
        cache_key = f"{text}_{max_width}"
        if cache_key in self._render_cache:
            return self._render_cache[cache_key].copy()

        # Wrap text if max_width specified
        if max_width:
            text = self._hard_wrap_text(text, max_width)

        # Process lines
        lines = text.split("\n")
        line_infos = []
        max_line_width = 0
        total_height = 0

        for line in lines:
            segments = self._split_text_and_emojis(line)
            line_width = 0
            line_height = 0
            seg_info = []

            for seg_text, is_emoji_seg in segments:
                if not seg_text:
                    continue

                font = self.emoji_font if is_emoji_seg else self.text_font
                bbox = font.getbbox(seg_text)
                seg_width = bbox[2] - bbox[0]
                seg_height = bbox[3] - bbox[1]

                # Slight vertical adjustment for emojis
                y_adjust = int(self.font_size * 0.1) if is_emoji_seg else 0

                seg_info.append({
                    "text": seg_text,
                    "is_emoji": is_emoji_seg,
                    "width": seg_width,
                    "height": seg_height,
                    "bbox": bbox,
                    "y_adjust": y_adjust
                })

                line_width += seg_width
                line_height = max(line_height, seg_height)

            line_infos.append({"segments": seg_info, "width": line_width, "height": line_height})
            max_line_width = max(max_line_width, line_width)
            total_height += line_height + 5  # 5px line spacing

        # Create image
        padding = self.outline_width * 2 + 10
        img_width = max_line_width + padding * 2
        img_height = total_height + padding * 2
        img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Render lines
        y = padding
        for line_info in line_infos:
            x = padding + (max_line_width - line_info["width"]) // 2  # Center align
            baseline = y + line_info["height"]

            for seg in line_info["segments"]:
                font = self.emoji_font if seg["is_emoji"] else self.text_font
                seg_y = baseline - seg["bbox"][3] + seg["y_adjust"]

                if seg["is_emoji"]:
                    # Render emoji with embedded color
                    draw.text(
                        (x, seg_y),
                        seg["text"],
                        font=font,
                        fill=self.text_color + (255,),
                        embedded_color=True
                    )
                else:
                    # Render outline
                    if self.outline_width > 0:
                        for dx in range(-self.outline_width, self.outline_width + 1):
                            for dy in range(-self.outline_width, self.outline_width + 1):
                                if dx != 0 or dy != 0:
                                    draw.text(
                                        (x + dx, seg_y + dy),
                                        seg["text"],
                                        font=font,
                                        fill=self.outline_color + (255,),
                                        embedded_color=False
                                    )

                    # Render text
                    draw.text(
                        (x, seg_y),
                        seg["text"],
                        font=font,
                        fill=self.text_color + (255,),
                        embedded_color=False
                    )

                x += seg["width"]

            y += line_info["height"] + 5

        # Convert to BGRA numpy array (for OpenCV)
        arr = np.array(img)
        bgra = arr.copy()
        bgra[:, :, 0] = arr[:, :, 2]  # Swap R and B
        bgra[:, :, 2] = arr[:, :, 0]

        # Cache if reasonable size (< 50MB)
        if bgra.nbytes < 50 * 1024 * 1024:
            self._render_cache[cache_key] = bgra.copy()

        return bgra


def overlay_text_on_frame(
    frame: np.ndarray,
    text_img: np.ndarray,
    position: str = "center",
    margin_pct: float = 0.16
) -> np.ndarray:
    """
    Overlay rendered text image onto video frame.

    Args:
        frame: Video frame (BGR or BGRA)
        text_img: Rendered text image (BGRA with alpha)
        position: Position ("center", "top", "bottom")
        margin_pct: Margin percentage from edges

    Returns:
        Frame with text overlay
    """
    if text_img is None or text_img.size == 0:
        return frame

    frame_height, frame_width = frame.shape[:2]
    text_height, text_width = text_img.shape[:2]

    # Scale down text if too large
    if text_height > frame_height or text_width > frame_width:
        scale = min(frame_height / float(text_height), frame_width / float(text_width)) * 0.9
        new_width = max(1, int(text_width * scale))
        new_height = max(1, int(text_height * scale))
        text_img = cv2.resize(text_img, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
        text_height, text_width = text_img.shape[:2]

    # Calculate position
    margin_x = int(frame_width * margin_pct)
    margin_y = int(frame_height * margin_pct)

    if position == "center":
        x = (frame_width - text_width) // 2
        y = (frame_height - text_height) // 2
    elif position == "bottom":
        x = (frame_width - text_width) // 2
        y = frame_height - text_height - margin_y
    elif position == "top":
        x = (frame_width - text_width) // 2
        y = margin_y
    else:
        x, y = position  # Custom position tuple

    # Clamp to frame bounds
    x = max(0, min(x, frame_width - text_width))
    y = max(0, min(y, frame_height - text_height))

    # Alpha blending
    if frame.shape[2] == 3 and text_img.shape[2] == 4:
        roi = frame[y:y + text_height, x:x + text_width]
        alpha = text_img[:, :, 3:4] / 255.0

        for c in range(3):
            roi[:, :, c] = (
                roi[:, :, c] * (1 - alpha[:, :, 0]) +
                text_img[:, :, c] * alpha[:, :, 0]
            )

        frame[y:y + text_height, x:x + text_width] = roi

    return frame
