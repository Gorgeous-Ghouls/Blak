import enum
from pathlib import Path


class Colors(enum.Enum):
    """A class that defines the color pallet used in the app"""

    primary_bg = "#2C3639"
    accent_bg = "#3F4E4F"
    text = "#000000"
    text_medium = "#DCD7C9"
    text_dark = "#A27B5C"


app_dir = Path(__file__).parents[1]  # the app directory
