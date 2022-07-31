from pathlib import Path

from kivy.animation import Animation
from kivy.event import EventDispatcher
from kivy.properties import ColorProperty
from kivy.utils import get_color_from_hex


class ColorsBase(EventDispatcher):
    """A class that defines the color pallet used in the app"""

    primary_bg = ColorProperty(defaultvalue="#2C3639")
    primary_bg_text = ColorProperty(defaultvalue="#2d383b")
    accent_bg = ColorProperty(defaultvalue="#3F4E4F")
    accent_bg_text = ColorProperty(defaultvalue="#576a6b")
    text = ColorProperty(defaultvalue="#FFFFFF")
    text_medium = ColorProperty(defaultvalue="#DCD7C9")
    text_dark = ColorProperty(defaultvalue="#A27B5C")
    button_bg = ColorProperty(defaultvalue="#5b7071")

    def reset(self):
        """Reset the value of colors to default"""
        kwargs = {"duration": 0.2}
        for var in [
            i
            for i in ColorsBase.__dict__.keys()
            if not any(map(i.startswith, ["_", "reset"]))
        ]:
            kwargs.update(
                {var: get_color_from_hex(getattr(ColorsBase, var).defaultvalue)}
            )
        anim = Animation(**kwargs)
        anim.start(self)


Colors = ColorsBase()


app_dir = Path(__file__).parents[1]  # the app directory
