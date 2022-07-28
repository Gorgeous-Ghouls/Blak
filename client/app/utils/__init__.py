import enum
from pathlib import Path

from kivy.utils import get_color_from_hex


class Colors(enum.Enum):
    """A class that defines the color pallet used in the app"""

    primary_bg = "2C3639"
    primary_bg_text = "2d383b"
    accent_bg = "3F4E4F"
    accent_bg_text = "576a6b"
    text = "000000"
    text_medium = "DCD7C9"
    text_dark = "A27B5C"

    @staticmethod
    def get_kivy_color(color: str) -> list[float]:
        """Returns kivy compatible colors"""
        if hasattr(Colors, color):
            return get_color_from_hex(getattr(Colors, color).value)

    # todo make Colors class be kivy compatible by default


app_dir = Path(__file__).parents[1]  # the app directory
