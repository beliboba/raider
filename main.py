import asyncio
import logging

import nest_asyncio

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.logging import TextualHandler
from textual.validation import Number, Regex
from textual.widgets import Input, Label, TextArea, Checkbox, Button

from bots import start


logging.basicConfig(
    level="INFO",
    handlers=[TextualHandler()],
)


class ControlApp(App):
    CSS_PATH = "misc/style.tcss"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Container(
            Container(
                Label("Ссылка на конференцию:"),
                Input(
                    placeholder="https://meet.jit.si/...",
                    classes="centered",
                    id="url",
                    validators=Regex(r"https://meet\.jit\.si/[a-zA-Z0-9]*")
                ),
            ),
            Container(
                Label("Количество ботов:"),
                Input(
                    placeholder="4",
                    validators=Number(minimum=1),
                    id="bot_num"
                )
            ),
            Container(
                Label("Сообщения:"),
                TextArea("New line = new message", id="messages"),
                Checkbox("Случайные сообщения?", False, id="random_messages"),
                Label("Сообщений на бота | -1=бесконечность, 0=не отправлять сообщения"),
                Input(
                    placeholder="10",
                    validators=Number(minimum=-1),
                    id="message_num"
                )
            ),
            Container(
                Label("Имена ботов:"),
                Input(placeholder="Bot", id="username"),
                Checkbox("Добавлять цифры?", True, id="add_numbers"),
                Checkbox("Включить камеру?", False, id="cam_switch"),
                Checkbox("Включить микрофон?", False, id="mic_switch")
            ),
            Container(
                Label("Приколы (требуются права модератора):"),
                Checkbox("Выгонять участников?", False, id="kick"),
                Checkbox("Заглушать участников?", False, id="mute"),
                Checkbox("Выключать камеры участникам?", False, id="cam"),
                Checkbox("Включать видео с YouTube?", False, id="yt"),
                Input(placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ", id="yt_url")
            ),
            Container(
                Button("Пуск", variant="success", id="start"),
                Button("Стоп", variant="error", id="stop")
            ),
            classes="settings"
        )

    @on(Button.Pressed, "#start")
    def start(self):
        try:
            data = {
                "url": self.query_one("#url").value,
                "bot_num": int(self.query_one("#bot_num").value),
                "messages": self.query_one("#messages").text if self.query_one("#messages").text else " ",
                "message_num": int(self.query_one("#message_num").value),
                "messages_random": bool(self.query_one("#random_messages").value),
                "username": self.query_one("#username").value,
                "add_numbers": bool(self.query_one("#add_numbers").value),
                "kick": bool(self.query_one("#kick").value),
                "mute": bool(self.query_one("#mute").value),
                "disable_cam": bool(self.query_one("#cam").value),
                "yt": bool(self.query_one("#yt").value),
                "yt_url": self.query_one("#yt_url").value,
                "mic_switch": bool(self.query_one("#mic_switch").value),
                "cam_switch": bool(self.query_one("#cam_switch").value)
            }
        except (ValueError, TypeError):
            return

        bots = self.loop.run_until_complete(start(data))
        self.bots.extend([asyncio.ensure_future(bot.start()) for bot in bots])
        logging.debug("TEST")

    @on(Button.Pressed, "#stop")
    def stop(self):
        for bot in self.bots:
            bot.cancel()
        self.bots = []

    def __init__(self):
        super().__init__()
        self.bots: list = []
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()


if __name__ == "__main__":
    nest_asyncio.apply()
    app = ControlApp()
    app.run()
