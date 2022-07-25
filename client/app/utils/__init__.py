import enum
from pathlib import Path

from kivy.utils import deprecated, get_color_from_hex


class Colors(enum.Enum):
    """A class that defines the color pallet used in the app"""

    primary_bg = "#2C3639"
    accent_bg = "#3F4E4F"
    accent_bg_text = "#576a6b"
    text = "#000000"
    text_medium = "#DCD7C9"
    text_dark = "#A27B5C"

    @deprecated(msg="This function will be removed in next minor version")
    @staticmethod
    def get_kivy_color(color: str) -> list[float]:
        """Returns kivy compatible colors"""
        if hasattr(Colors, color):
            return get_color_from_hex(getattr(Colors, color).value)

    # todo


app_dir = Path(__file__).parents[1]  # the app directory
