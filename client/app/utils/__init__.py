from pathlib import Path

from kivy.event import EventDispatcher
from kivy.properties import ColorProperty


class ColorsBase(EventDispatcher):
    """A class that defines the color pallet used in the app"""

    primary_bg = ColorProperty(defaultvalue="#2C3639")
    primary_bg_text = ColorProperty(defaultvalue="#2d383b")
    accent_bg = ColorProperty(defaultvalue="#3F4E4F")
    accent_bg_text = ColorProperty(defaultvalue="#576a6b")
    text = ColorProperty(defaultvalue="#000000")
    text_medium = ColorProperty(defaultvalue="#DCD7C9")
    text_dark = ColorProperty(defaultvalue="#A27B5C")

    def reset(self):
        """Reset the value of colors to default"""
        for var in [
            i
            for i in ColorsBase.__dict__.keys()
            if not any(map(i.startswith, ["_", "reset"]))
        ]:
            setattr(self, var, getattr(ColorsBase, var).defaultvalue)


Colors = ColorsBase()


app_dir = Path(__file__).parents[1]  # the app directory
