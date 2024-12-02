#!/usr/bin/env python3
import curses
import sys
import os
import subprocess
from datetime import datetime
from .pkm_manager import PKMManager
from .themes import ThemeManager

class MenuUI:
    def __init__(self):
        self.pkm = PKMManager()
        self.theme_manager = ThemeManager()
        self.menu_items = [
            # Core PKM Features
            ("Daily Journal", "Edit today's journal"),
            ("Daily Metrics", "Track mood, energy & sleep"),
            ("Sub-Daily Metrics", "Track current mood & energy"),
            ("Work Hours", "Log work time"),
            ("Habits", "Track daily habits"),
            ("Alcohol Log", "Track consumption"),
            ("Recent Logs", "View recent entries"),
            ("Query DB", "View statistics"),
            
            # System Management
            ("Web Interface", "Launch web application"),
            ("Configuration", "System settings"),
            ("Backup DB", "Create database backup"),
            ("Restore DB", "Load database backup"),
            ("Backup MD", "Save markdown files"),
            ("Restore MD", "Load markdown files"),
            ("Exit", "Close PKM")
        ]
        self.current_row = 0

    def execute_command(self, command):
        """Execute a shell command and return its output"""
        try:
            result = subprocess.run(command, shell=True, check=True, 
                                 capture_output=True, text=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}"

    def check_web_config(self):
        """Check web configuration and return port number"""
        config_file = "pkm/web/config.json"
        if not os.path.exists(config_file):
            return None, "Web configuration file not found."
        
        try:
            import json
            with open(config_file, 'r') as f:
                config = json.load(f)
                if not config.get('web_enabled'):
                    return None, "Web interface is not enabled in config."
                return config.get('port'), None
        except Exception as e:
            return None, f"Error reading config: {str(e)}"

    def safe_addstr(self, stdscr, y, x, text, attr=0):
        """Safely add a string to the screen, handling window boundaries"""
        height, width = stdscr.getmaxyx()
        if y < height and x < width:
            try:
                # Truncate text if it would exceed screen width
                max_length = width - x
                if len(text) > max_length:
                    text = text[:max_length]
                stdscr.addstr(y, x, text, attr)
            except curses.error:
                pass

    def draw_menu(self, stdscr):
        self.stdscr = stdscr
        # Initialize theme colors
        self.theme_manager.init_colors()
        theme_color = self.theme_manager.get_theme_color()
        
        # Hide cursor
        curses.curs_set(0)

        while True:
            # Get window dimensions
            height, width = stdscr.getmaxyx()
            
            # Clear screen
            stdscr.clear()

            # Calculate menu width and position
            menu_width = min(50, width - 4)
            x_offset = max(2, (width - menu_width) // 2)
            y_offset = 3

            # Draw title
            title = "Personal Knowledge Management System"
            x_title = max(0, (width - len(title)) // 2)
            self.safe_addstr(stdscr, 1, x_title, title, theme_color | curses.A_BOLD)

            # Draw menu items
            for idx, (item, desc) in enumerate(self.menu_items):
                y = y_offset + idx
                
                if y >= height - 1:  # Stop if we've reached bottom of screen
                    break
                    
                if idx == self.current_row:
                    self.safe_addstr(stdscr, y, x_offset, "> " + item, theme_color | curses.A_BOLD)
                else:
                    self.safe_addstr(stdscr, y, x_offset, "  " + item)

            stdscr.refresh()

            # Handle key input
            key = stdscr.getch()
            if key == curses.KEY_UP and self.current_row > 0:
                self.current_row -= 1
            elif key == curses.KEY_DOWN and self.current_row < len(self.menu_items) - 1:
                self.current_row += 1
            elif key == ord('\n'):  # Enter key
                return self.current_row
            elif key in (ord('q'), ord('Q')):
                return len(self.menu_items) - 1  # Exit option
            elif key == curses.KEY_RESIZE:
                stdscr.clear()

def main():
    menu = MenuUI()
    selected = curses.wrapper(menu.draw_menu)
    
    # Map selection to action
    if selected == 0:  # Daily Journal
        from .pkm_cli import PKMApp
        app = PKMApp()
        app.run()
    elif selected == 1:  # Daily Metrics
        from .pkm_cli import PKMApp
        app = PKMApp()
        app.run()
    elif selected == 2:  # Sub-Daily Metrics
        from .pkm_cli import PKMApp
        app = PKMApp()
        app.run()
    elif selected == 3:  # Work Hours
        from .pkm_cli import PKMApp
        app = PKMApp()
        app.run()
    elif selected == 4:  # Habits
        from .pkm_cli import PKMApp
        app = PKMApp()
        app.run()
    elif selected == 5:  # Alcohol Log
        from .pkm_cli import PKMApp
        app = PKMApp()
        app.run()
    elif selected == 6:  # Recent Logs
        from .pkm_cli import PKMApp
        app = PKMApp()
        app.run()
    elif selected == 7:  # Query DB
        from .pkm_cli import PKMApp
        app = PKMApp()
        app.run()
    elif selected == 8:  # Web Interface
        port, error = menu.check_web_config()
        if error:
            print(f"Error: {error}")
            sys.exit(1)
        print(f"Starting web interface on port {port}...")
        os.system(f"python3 -m pkm.web.app")
    elif selected == 9:  # Configuration
        os.system("python3 -m pkm.config_menu")
    elif selected == 10:  # Backup DB
        os.system("./pkm.sh backup-db")
    elif selected == 11:  # Restore DB
        os.system("./pkm.sh restore-db")
    elif selected == 12:  # Backup MD
        os.system("./pkm.sh backup-md")
    elif selected == 13:  # Restore MD
        os.system("./pkm.sh restore-md")
    elif selected == 14:  # Exit
        sys.exit(0)

if __name__ == "__main__":
    main()
