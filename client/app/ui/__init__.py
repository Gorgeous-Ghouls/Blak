from kivymd.app import MDApp
from kivymd.uix.card import MDCard


class ChatItem(MDCard):
    """Class representing a chat."""

    # ask can I use dataclass here somehow ? the args in __init__ need to be set before super call

    def __init__(
        self,
        username: str,
        custom_id: str,
        last_seen: str = "",
        msg_count: str = "",
        **kwargs
    ):

        self.username = username
        self.custom_id = custom_id
        self.last_seen = last_seen
        self.msg_count = msg_count
        super(ChatItem, self).__init__()

    def on_touch_up(self, touch):
        """Event Fired everytime mouse is released to tap is released."""
        if self.collide_point(*touch.pos):
            MDApp.get_running_app().root.ids[
                "screen_manager"
            ].current = self.custom_id  # switch screen to the chat
