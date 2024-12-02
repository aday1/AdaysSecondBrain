import curses
import os
import subprocess
import json
from .themes import ThemeManager

class ConfigMenu:
    def __init__(self):
        self.theme_manager = ThemeManager()
        self.current_selection = 0
        self.menu_items = [
            "Web Interface Settings",
            "Database Settings",
            "Backup Settings",
            "Exit"
        ]
        self.web_server_process = None
        self.web_config_path = os.path.join(os.path.dirname(__file__), 'web', 'config.json')

    def load_web_config(self):
        try:
            with open(self.web_config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            return None

    def save_web_config(self, config):
        try:
            with open(self.web_config_path, 'w') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            return False

    def draw_menu(self, stdscr, title, items, current_selection):
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        # Draw title
        x = w//2 - len(title)//2
        try:
            stdscr.addstr(1, x, title, self.theme_manager.get_theme_color())
        except curses.error:
            pass
        
        # Draw menu items
        for idx, item in enumerate(items):
            try:
                x = w//2 - len(item)//2
                y = h//2 - len(items)//2 + idx
                
                if idx == current_selection:
                    stdscr.attron(curses.A_REVERSE | self.theme_manager.get_theme_color())
                stdscr.addstr(y, x, item)
                if idx == current_selection:
                    stdscr.attroff(curses.A_REVERSE | self.theme_manager.get_theme_color())
            except curses.error:
                pass
        
        # Draw instructions
        try:
            instructions = "Use ↑↓ arrows to navigate, Enter to select, 'q' to quit"
            x = w//2 - len(instructions)//2
            stdscr.addstr(h-2, x, instructions, self.theme_manager.get_theme_color())
        except curses.error:
            pass
        
        stdscr.refresh()

    def configure_port(self, stdscr):
        """Configure web server port"""
        config = self.load_web_config()
        if not config:
            stdscr.addstr(stdscr.getmaxyx()[0]-3, 2, "Error loading config! Press any key...",
                         self.theme_manager.get_theme_color())
            stdscr.getch()
            return

        current_port = str(config.get('port', 5000))
        new_port = ""
        cursor_pos = 0
        h, w = stdscr.getmaxyx()

        while True:
            stdscr.clear()
            title = "Configure Web Server Port"
            x = w//2 - len(title)//2
            stdscr.addstr(1, x, title, self.theme_manager.get_theme_color())

            prompt = f"Enter new port (current: {current_port}): "
            input_y = h//2
            input_x = w//2 - len(prompt)//2
            stdscr.addstr(input_y, input_x, prompt)
            stdscr.addstr(input_y, input_x + len(prompt), new_port)
            
            instructions = "Enter numbers, Backspace to delete, Enter to confirm, 'q' to cancel"
            x = w//2 - len(instructions)//2
            stdscr.addstr(h-2, x, instructions, self.theme_manager.get_theme_color())
            
            stdscr.move(input_y, input_x + len(prompt) + cursor_pos)
            stdscr.refresh()

            key = stdscr.getch()
            if key == ord('q'):
                return
            elif key == ord('\n'):  # Enter key
                if new_port.isdigit() and 1024 <= int(new_port) <= 65535:
                    config['port'] = int(new_port)
                    if self.save_web_config(config):
                        stdscr.addstr(h-3, 2, f"Port updated to {new_port}! Press any key...",
                                    self.theme_manager.get_theme_color())
                    else:
                        stdscr.addstr(h-3, 2, "Error saving config! Press any key...",
                                    self.theme_manager.get_theme_color())
                    stdscr.getch()
                    return
                else:
                    stdscr.addstr(h-3, 2, "Invalid port! Must be between 1024-65535. Press any key...",
                                self.theme_manager.get_theme_color())
                    stdscr.getch()
            elif key == curses.KEY_BACKSPACE or key == 127:  # Backspace
                if cursor_pos > 0:
                    new_port = new_port[:-1]
                    cursor_pos -= 1
            elif 48 <= key <= 57 and len(new_port) < 5:  # Numbers 0-9
                new_port += chr(key)
                cursor_pos += 1

    def web_interface_menu(self, stdscr):
        """Display web interface settings menu"""
        menu_items = [
            "Start Web Server",
            "Stop Web Server",
            "Configure Port",
            "Back to Main Menu"
        ]
        current_selection = 0
        
        while True:
            self.draw_menu(stdscr, "Web Interface Settings", menu_items, current_selection)
            
            key = stdscr.getch()
            if key == ord('q'):
                break
            elif key == curses.KEY_UP and current_selection > 0:
                current_selection -= 1
            elif key == curses.KEY_DOWN and current_selection < len(menu_items) - 1:
                current_selection += 1
            elif key == ord('\n'):
                if current_selection == len(menu_items) - 1:  # Back to Main Menu
                    break
                elif current_selection == 0:  # Start Web Server
                    if not self.web_server_process:
                        config = self.load_web_config()
                        if config:
                            try:
                                port = str(config.get('port', 5000))
                                self.web_server_process = subprocess.Popen(
                                    ['python', '-m', 'pkm.web.app', '--port', port]
                                )
                                stdscr.addstr(stdscr.getmaxyx()[0]-3, 2, 
                                            f"Web server started on port {port}! Press any key...",
                                            self.theme_manager.get_theme_color())
                            except Exception as e:
                                stdscr.addstr(stdscr.getmaxyx()[0]-3, 2, 
                                            f"Error starting server: {str(e)}",
                                            self.theme_manager.get_theme_color())
                        else:
                            stdscr.addstr(stdscr.getmaxyx()[0]-3, 2, 
                                        "Error loading config! Press any key...",
                                        self.theme_manager.get_theme_color())
                        stdscr.getch()
                elif current_selection == 1:  # Stop Web Server
                    self.stop_web_server()
                    stdscr.addstr(stdscr.getmaxyx()[0]-3, 2, "Web server stopped! Press any key...",
                                self.theme_manager.get_theme_color())
                    stdscr.getch()
                elif current_selection == 2:  # Configure Port
                    self.configure_port(stdscr)

    def database_menu(self, stdscr):
        """Display database settings menu"""
        menu_items = [
            "Initialize Database",
            "Backup Database",
            "Restore Database",
            "Back to Main Menu"
        ]
        current_selection = 0
        
        while True:
            self.draw_menu(stdscr, "Database Settings", menu_items, current_selection)
            
            key = stdscr.getch()
            if key == ord('q'):
                break
            elif key == curses.KEY_UP and current_selection > 0:
                current_selection -= 1
            elif key == curses.KEY_DOWN and current_selection < len(menu_items) - 1:
                current_selection += 1
            elif key == ord('\n'):
                if current_selection == len(menu_items) - 1:  # Back to Main Menu
                    break
                elif current_selection == 0:  # Initialize Database
                    curses.endwin()  # Temporarily suspend curses
                    os.system('./pkm.sh init-db')
                    stdscr.getch()  # Wait for user input before returning to menu
                    curses.doupdate()  # Refresh the screen
                elif current_selection == 1:  # Backup Database
                    curses.endwin()  # Temporarily suspend curses
                    os.system('./pkm.sh backup-db')
                    stdscr.getch()  # Wait for user input before returning to menu
                    curses.doupdate()  # Refresh the screen
                elif current_selection == 2:  # Restore Database
                    curses.endwin()  # Temporarily suspend curses
                    os.system('./pkm.sh restore-db')
                    stdscr.getch()  # Wait for user input before returning to menu
                    curses.doupdate()  # Refresh the screen

    def backup_menu(self, stdscr):
        """Display backup settings menu"""
        menu_items = [
            "Configure Backup Location",
            "Schedule Automatic Backups",
            "Run Manual Backup",
            "Back to Main Menu"
        ]
        current_selection = 0
        
        while True:
            self.draw_menu(stdscr, "Backup Settings", menu_items, current_selection)
            
            key = stdscr.getch()
            if key == ord('q'):
                break
            elif key == curses.KEY_UP and current_selection > 0:
                current_selection -= 1
            elif key == curses.KEY_DOWN and current_selection < len(menu_items) - 1:
                current_selection += 1
            elif key == ord('\n'):
                if current_selection == len(menu_items) - 1:  # Back to Main Menu
                    break
                elif current_selection == 2:  # Run Manual Backup
                    curses.endwin()  # Temporarily suspend curses
                    os.system('./pkm.sh backup-db')
                    stdscr.getch()  # Wait for user input before returning to menu
                    curses.doupdate()  # Refresh the screen

    def stop_web_server(self):
        if self.web_server_process:
            self.web_server_process.terminate()
            self.web_server_process = None

    def main(self, stdscr):
        # Initialize colors
        self.theme_manager.init_colors()
        curses.curs_set(0)
        stdscr.keypad(1)
        
        while True:
            self.draw_menu(stdscr, "PKM System Configuration", self.menu_items, self.current_selection)
            
            key = stdscr.getch()
            
            if key == ord('q'):
                # Clean up web server if running
                self.stop_web_server()
                break
            elif key == curses.KEY_UP and self.current_selection > 0:
                self.current_selection -= 1
            elif key == curses.KEY_DOWN and self.current_selection < len(self.menu_items) - 1:
                self.current_selection += 1
            elif key == ord('\n'):
                if self.current_selection == 0:
                    self.web_interface_menu(stdscr)
                elif self.current_selection == 1:
                    self.database_menu(stdscr)
                elif self.current_selection == 2:
                    self.backup_menu(stdscr)
                elif self.current_selection == 3:
                    # Clean up web server if running
                    self.stop_web_server()
                    break


if __name__ == "__main__":
    config_menu = ConfigMenu()
    curses.wrapper(config_menu.main)
