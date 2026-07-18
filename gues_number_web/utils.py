import os
from colorama import init, Fore, Style
from datetime import datetime

init(autoreset=True)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def colorize(text, color='white'):
    colors = {
        'red': Fore.RED,
        'green': Fore.GREEN,
        'yellow': Fore.YELLOW,
        'blue': Fore.BLUE,
        'cyan': Fore.CYAN,
        'white': Fore.WHITE
    }
    return colors.get(color, Fore.WHITE) + text + Style.RESET_ALL
def current_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")