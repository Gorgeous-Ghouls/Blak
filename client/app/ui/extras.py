import random

from app.utils import app_dir
from kivy._clock import ClockEvent
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.image import Image
from kivy.uix.layout import Layout
from kivy.utils import get_random_color


class Bugs:
    """Class of bugs"""

    callbacks: list[ClockEvent] = []
    bugs: list[Image] = []

    def __init__(self):
        self.source = str(app_dir / "ui/static/bug.png")

    def add_bug(self, parent: Layout):
        """Adds bugs to the parent layout"""
        img = Image(source=self.source)
        img.x = random.randint(0, Window.size[0])
        img.y = random.randint(0, Window.size[1])
        img.size_hint = None, None
        img.size = (dp(20), dp(20))
        img.color = get_random_color()
        Bugs.callbacks.append(
            Clock.schedule_interval(lambda dt: self.animate_color(img), 1)
        )
        Bugs.bugs.append(img)
        parent.add_widget(img)

    @staticmethod
    def animate_color(img: Image):
        """Changes color and position of bugs"""
        anim = Animation(
            color=get_random_color(),
            x=img.x + random.randint(-5, 5),
            y=img.y + random.randint(-5, 5),
            duration=0.5,
        )
        anim.start(img)

    @staticmethod
    def clear_bugs():
        """Removes all the bugs..."""
        for callback in Bugs.callbacks:
            callback.cancel()
        for bug in Bugs.bugs:
            bug.parent.remove_widget(
                bug
            )  # asking your parent to remove you, smh sad life of a bug :(
