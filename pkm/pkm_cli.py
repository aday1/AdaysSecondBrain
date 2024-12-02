#!/usr/bin/env python3
from textual.app import App
from textual.widgets import Button, Header, Footer, Static
from textual.containers import Container, ScrollableContainer
from textual.screen import Screen
from textual.binding import Binding
import os
from .pkm_manager import PKMManager

EMOJI_JOURNAL = "📔"
EMOJI_METRICS = "📊"
EMOJI_WORK = "💼"
EMOJI_HABITS = "✅"
EMOJI_ALCOHOL = "🍷"
EMOJI_LOGS = "📚"
EMOJI_QUERY = "🔍"
EMOJI_EXIT = "🚪"

class ActionScreen(Screen):
    def __init__(self, title: str, content: str):
        super().__init__()
        self.title = title
        self.content = content

    def compose(self):
        yield Header(self.title)
        yield ScrollableContainer(
            Static(self.content),
            classes="content-container"
        )
        yield Footer()

class PKMApp(App):
    CSS = """
    Screen {
        align: center middle;
    }

    .menu-container {
        width: 50;
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    .content-container {
        width: 90%;
        height: 80%;
        border: solid $accent;
        padding: 1;
        margin: 1;
        overflow-y: scroll;
    }

    Button {
        width: 100%;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("b", "go_back", "Back")
    ]

    def __init__(self):
        super().__init__()
        self.pkm = PKMManager()

    def compose(self):
        yield Header()
        yield Container(
            Button(f"{EMOJI_JOURNAL} Edit Daily Journal", id="journal"),
            Button(f"{EMOJI_METRICS} Track Metrics", id="metrics"),
            Button(f"{EMOJI_WORK} Log Work", id="work"),
            Button(f"{EMOJI_HABITS} Track Habits", id="habits"),
            Button(f"{EMOJI_ALCOHOL} Log Alcohol", id="alcohol"),
            Button(f"{EMOJI_LOGS} View Logs", id="logs"),
            Button(f"{EMOJI_QUERY} Query DB", id="query"),
            Button(f"{EMOJI_EXIT} Exit", id="exit"),
            classes="menu-container"
        )
        yield Footer()

    def action_go_back(self):
        """Go back to the main menu"""
        self.pop_screen()

    def show_action_screen(self, title: str, content: str):
        """Show a screen for a specific action"""
        self.push_screen(ActionScreen(title, content))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        button_id = event.button.id
        if button_id == "exit":
            self.exit()
        elif button_id == "journal":
            content = self.pkm.get_daily_journal()
            self.show_action_screen("Daily Journal", content)
        elif button_id == "metrics":
            content = self.pkm.get_metrics()
            self.show_action_screen("Daily Metrics", content)
        elif button_id == "work":
            content = self.pkm.get_work_log()
            self.show_action_screen("Work Log", content)
        elif button_id == "habits":
            content = self.pkm.get_habits()
            self.show_action_screen("Habits", content)
        elif button_id == "alcohol":
            content = self.pkm.get_alcohol_log()
            self.show_action_screen("Alcohol Log", content)
        elif button_id == "logs":
            content = self.pkm.get_recent_logs()
            self.show_action_screen("Recent Logs", content)
        elif button_id == "query":
            content = self.pkm.query_database()
            self.show_action_screen("Database Query", content)

def run():
    app = PKMApp()
    app.run()

if __name__ == "__main__":
    run()
