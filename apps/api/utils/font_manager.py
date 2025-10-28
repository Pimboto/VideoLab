"""
Font management utilities for text and emoji rendering
"""
import logging
import platform
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Platform-specific emoji font paths
EMOJI_FONTS = {
    "windows": ["C:/Windows/Fonts/seguiemj.ttf", "C:/Windows/Fonts/SegoeUIEmoji.ttf"],
    "mac": ["/System/Library/Fonts/Apple Color Emoji.ttc"],
    "linux": ["/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"]
}

# Text font candidates (in order of preference)
TEXT_FONT_CANDIDATES = [
    "C:/USERS/JUAN ESTEBAN/APPDATA/LOCAL/MICROSOFT/WINDOWS/FONTS/FONNTS.COM-PROXIMA_NOVA_SEMIBOLD.OTF",
    "C:/Windows/Fonts/inter.ttf",
    "C:/Windows/Fonts/Inter-VariableFont_slnt,wght.ttf",
    "C:/Windows/Fonts/Arial.ttf"
]


def find_emoji_font() -> str:
    """
    Find system emoji font.

    Returns:
        Path to emoji font

    Raises:
        FileNotFoundError: If no emoji font is found
    """
    system_name = platform.system().lower()

    # Try platform-specific fonts first
    if system_name == "windows":
        fonts = EMOJI_FONTS["windows"]
    elif system_name == "darwin":
        fonts = EMOJI_FONTS["mac"]
    else:
        fonts = EMOJI_FONTS["linux"]

    for font_path in fonts:
        if Path(font_path).exists():
            logger.info(f"Found emoji font: {font_path}")
            return font_path

    # Fallback: try all platform fonts
    for font_list in EMOJI_FONTS.values():
        for font_path in font_list:
            if Path(font_path).exists():
                logger.warning(f"Using fallback emoji font: {font_path}")
                return font_path

    raise FileNotFoundError(
        "No emoji font found. Install Segoe UI Emoji (Windows) or Noto Color Emoji (Linux)."
    )


def find_text_font(custom_path: Optional[str] = None) -> str:
    """
    Find text font for rendering.

    Args:
        custom_path: Optional custom font path

    Returns:
        Path to text font
    """
    # Use custom font if provided and exists
    if custom_path and Path(custom_path).exists():
        logger.info(f"Using custom text font: {custom_path}")
        return custom_path

    # Try font candidates
    for font_path in TEXT_FONT_CANDIDATES:
        if Path(font_path).exists():
            logger.info(f"Found text font: {font_path}")
            return font_path

    # Fallback to emoji font
    logger.warning("No text font found, using emoji font as fallback")
    return find_emoji_font()
