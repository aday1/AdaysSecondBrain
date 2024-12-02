#!/usr/bin/env python3
import curses
import random
import time
from threading import Thread
import json
import os

# Unicode box drawing characters for ASCII art mode
BOX_CHARS = {
    'top_left': '╔', 'top_right': '╗', 'bottom_left': '╚', 'bottom_right': '╝',
    'horizontal': '═', 'vertical': '║', 'title_left': '╟', 'title_right': '╢'
}

# CGA color pairs (background, foreground)
CGA_COLORS = [
    (0, 7),   # Black, Light Gray
    (0, 15),  # Black, White
    (1, 15),  # Blue, White
    (2, 15),  # Green, White
    (3, 15),  # Cyan, White
    (4, 15),  # Red, White
    (5, 15),  # Magenta, White
    (6, 15),  # Brown, White
]

# EGA color pairs
EGA_COLORS = [
    (0, 7),   # Black, Light Gray
    (0, 15),  # Black, White
    (1, 14),  # Blue, Yellow
    (2, 13),  # Green, Magenta
    (3, 12),  # Cyan, Red
    (4, 11),  # Red, Cyan
    (5, 10),  # Magenta, Green
    (6, 9),   # Brown, Light Blue
]

class ThemeManager:
    def __init__(self):
        self.current_theme = "default"
        self.animation_thread = None
        self.stop_animation = False
        self.text_size = "normal"
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'theme_config.json')
        self.whacky_colors = None
        self.load_config()

    def load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()  # Remove any whitespace
                if content:
                    config = json.loads(content)
                    self.current_theme = config.get('theme', 'default')
                    self.text_size = config.get('text_size', 'normal')
                else:
                    self.save_config()  # Create default config if file is empty
        except (FileNotFoundError, json.JSONDecodeError):
            self.save_config()

    def save_config(self):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump({
                'theme': self.current_theme,
                'text_size': self.text_size
            }, f)

    def init_colors(self):
        curses.start_color()
        curses.use_default_colors()
        
        # Basic themes
        curses.init_pair(1, curses.COLOR_WHITE, -1)  # default
        curses.init_pair(2, curses.COLOR_GREEN, -1)  # matrix
        curses.init_pair(3, curses.COLOR_CYAN, -1)   # wargames
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)  # high contrast
        
        # Initialize CGA colors
        for i, (bg, fg) in enumerate(CGA_COLORS, start=10):
            curses.init_pair(i, fg, bg)
        
        # Initialize EGA colors
        for i, (bg, fg) in enumerate(EGA_COLORS, start=20):
            curses.init_pair(i, fg, bg)
        
        # Random colors for whacky mode
        if curses.can_change_color() and curses.COLORS >= 256:
            self.whacky_colors = []
            for i in range(30, 40):
                fg = random.randint(0, 255)
                bg = random.randint(0, 255)
                curses.init_pair(i, fg, bg)
                self.whacky_colors.append(i)

    def get_theme_color(self):
        if self.current_theme == "matrix":
            return curses.color_pair(2)
        elif self.current_theme == "wargames":
            return curses.color_pair(3)
        elif self.current_theme == "high_contrast":
            return curses.color_pair(4)
        elif self.current_theme == "cga":
            return curses.color_pair(random.randint(10, 17))
        elif self.current_theme == "ega":
            return curses.color_pair(random.randint(20, 27))
        elif self.current_theme == "whacky":
            if self.whacky_colors:
                return curses.color_pair(random.choice(self.whacky_colors))
            return curses.color_pair(1)
        elif self.current_theme == "random":
            return curses.color_pair(random.randint(1, 4))
        elif self.current_theme == "crazy":
            return self.get_crazy_color()
        elif self.current_theme == "ascii":
            return curses.color_pair(1)
        else:  # default
            return curses.color_pair(1)

    def get_crazy_color(self):
        """Get a color for crazy mode based on current time"""
        colors = list(range(1, 5))
        index = int(time.time() * 2) % len(colors)
        return curses.color_pair(colors[index])

    def start_animation(self, stdscr):
        """Start the animation thread for crazy mode"""
        if self.animation_thread is None:
            self.stop_animation = False
            self.animation_thread = Thread(target=self._animate, args=(stdscr,))
            self.animation_thread.daemon = True
            self.animation_thread.start()

    def stop_animation(self):
        """Stop the animation thread"""
        if self.animation_thread is not None:
            self.stop_animation = True
            self.animation_thread.join()
            self.animation_thread = None

    def _animate(self, stdscr):
        """Animation loop for crazy mode"""
        h, w = stdscr.getmaxyx()
        while not self.stop_animation:
            try:
                # Draw animated border
                for y in range(h):
                    for x in range(w):
                        if y in (0, h-1) or x in (0, w-1):
                            color = self.get_crazy_color()
                            stdscr.addch(y, x, '█', color)
                stdscr.refresh()
                time.sleep(0.1)
            except curses.error:
                pass

    def apply_theme(self, stdscr, theme_name):
        """Apply the selected theme"""
        self.current_theme = theme_name
        self.save_config()
        
        # Stop any running animation
        self.stop_animation = True
        if self.animation_thread is not None:
            self.animation_thread.join()
            self.animation_thread = None
        
        # Clear screen
        stdscr.clear()
        
        # Start animation if crazy theme
        if theme_name == "crazy":
            self.start_animation(stdscr)
        
        # Generate new random colors for whacky theme
        if theme_name == "whacky":
            self.init_colors()

    def get_theme_names(self):
        """Get list of available themes"""
        return [
            "default",
            "matrix",
            "wargames",
            "high_contrast",
            "whacky",
            "cga",
            "ega",
            "ascii",
            "random",
            "crazy"
        ]

    def get_theme_description(self, theme_name):
        """Get description of a theme"""
        descriptions = {
            "default": "Classic terminal (white text on black)",
            "matrix": "The Matrix style (green text on black)",
            "wargames": "WarGames style (cyan text on black)",
            "high_contrast": "High contrast (black text on white)",
            "whacky": "Random but consistent colors",
            "cga": "Classic CGA color scheme",
            "ega": "Enhanced EGA color scheme",
            "ascii": "DOS-style box drawing characters",
            "random": "Random colors each time",
            "crazy": "Animated rainbow colors"
        }
        return descriptions.get(theme_name, "Unknown theme")

    def format_text(self, text):
        """Format text based on current text size"""
        if self.text_size == "big":
            return text.upper()
        elif self.text_size == "small":
            return text.lower()
        return text

    def draw_ascii_box(self, stdscr, y, x, height, width, title=""):
        """Draw a box using ASCII art characters"""
        try:
            # Draw corners
            stdscr.addstr(y, x, BOX_CHARS['top_left'])
            stdscr.addstr(y, x + width - 1, BOX_CHARS['top_right'])
            stdscr.addstr(y + height - 1, x, BOX_CHARS['bottom_left'])
            stdscr.addstr(y + height - 1, x + width - 1, BOX_CHARS['bottom_right'])
            
            # Draw horizontal lines
            for i in range(1, width - 1):
                stdscr.addstr(y, x + i, BOX_CHARS['horizontal'])
                stdscr.addstr(y + height - 1, x + i, BOX_CHARS['horizontal'])
            
            # Draw vertical lines
            for i in range(1, height - 1):
                stdscr.addstr(y + i, x, BOX_CHARS['vertical'])
                stdscr.addstr(y + i, x + width - 1, BOX_CHARS['vertical'])
            
            # Draw title if provided
            if title:
                title = f" {title} "
                title_x = x + (width - len(title)) // 2
                stdscr.addstr(y, title_x - 1, BOX_CHARS['title_left'])
                stdscr.addstr(y, title_x, title)
                stdscr.addstr(y, title_x + len(title), BOX_CHARS['title_right'])
        except curses.error:
            pass

    def set_text_size(self, size):
        """Set text size and save preference"""
        self.text_size = size
        self.save_config()

    def get_text_sizes(self):
        """Get available text sizes"""
        return ["small", "normal", "big"]
