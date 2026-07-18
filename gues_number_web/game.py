import random
import time
import json
import os
import glob
from datetime import datetime

# ================== Функции сохранения/загрузки ==================

def save_game(user, mode, difficulty, secret, attempts, guesses, low, high, hint_count=0, guess=None, start_time=None, time_limit=None):
    """Сохраняет текущее состояние игры в JSON-файл в папку data/saves/"""
    saves_dir = os.path.join('data', 'saves')
    os.makedirs(saves_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"save_{user}_{timestamp}.json"
    filepath = os.path.join(saves_dir, filename)

    game_state = {
        'user': user,
        'mode': mode,
        'difficulty': difficulty,
        'secret': secret,
        'attempts': attempts,
        'guesses': guesses,
        'low': low,
        'high': high,
        'hint_count': hint_count,
        'max_hints': 3,
        'guess': guess
    }
    if start_time is not None:
        game_state['start_time'] = start_time
    if time_limit is not None:
        game_state['time_limit'] = time_limit

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(game_state, f, indent=4, ensure_ascii=False)

    return filename

def list_saves(user):
    """Возвращает список файлов сохранений для указанного пользователя"""
    saves_dir = os.path.join('data', 'saves')
    if not os.path.exists(saves_dir):
        return []
    pattern = os.path.join(saves_dir, f"save_{user}_*.json")
    files = glob.glob(pattern)
    files.sort(reverse=True)
    return files

def load_game(filepath):
    """Загружает состояние игры из JSON-файла и возвращает словарь"""
    with open(filepath, 'r', encoding='utf-8') as f:
        game_state = json.load(f)
    return game_state

# ================== Функции создания новой игры ==================

def new_standard_game(difficulty):
    ranges = {'easy': (1,50), 'medium': (1,100), 'hard': (1,500)}
    low, high = ranges[difficulty]
    secret = random.randint(low, high)
    return {
        'mode': 'standard',
        'difficulty': difficulty,
        'secret': secret,
        'low': low,
        'high': high,
        'attempts': 0,
        'guesses': [],
        'hint_count': 0,
        'max_hints': 3,
        'game_over': False,
        'won': False
    }

def new_reverse_game(difficulty):
    ranges = {'easy': (1,50), 'medium': (1,100), 'hard': (1,500)}
    low, high = ranges[difficulty]
    guess = (low + high) // 2
    return {
        'mode': 'reverse',
        'difficulty': difficulty,
        'low': low,
        'high': high,
        'guess': guess,
        'attempts': 0,
        'game_over': False,
        'won': False
    }

def new_timed_game(difficulty, time_limit=60):
    """Создаёт начальное состояние для режима на время"""
    state = new_standard_game(difficulty)
    state['mode'] = 'timed'
    state['start_time'] = time.time()
    state['time_limit'] = time_limit
    return state

# ================== Функции обработки ходов ==================

def process_standard_guess(state, guess):
    """Обрабатывает ход в стандартном режиме. Возвращает (new_state, message, game_over)"""
    state['attempts'] += 1
    state['guesses'].append(guess)
    
    if guess == state['secret']:
        state['game_over'] = True
        state['won'] = True
        return state, f"Поздравляю! Вы угадали за {state['attempts']} попыток.", True
    elif guess < state['secret']:
        return state, "Загаданное число больше.", False
    else:
        return state, "Загаданное число меньше.", False

def process_reverse_guess(state, answer):
    """Обрабатывает ответ пользователя в обратном режиме. answer: '>', '<', '=' """
    if answer == '=':
        state['game_over'] = True
        state['won'] = True
        return state, f"Компьютер угадал за {state['attempts']} попыток.", True
    elif answer == '>':
        state['low'] = state['guess'] + 1
    elif answer == '<':
        state['high'] = state['guess'] - 1
    else:
        return state, "Некорректный ввод.", False
    
    state['attempts'] += 1
    if state['low'] > state['high']:
        state['game_over'] = True
        state['won'] = False
        return state, "Ошибка: диапазон пуст. Возможно, вы ошиблись.", True
    state['guess'] = (state['low'] + state['high']) // 2
    return state, f"Попытка {state['attempts']}: ваше число {state['guess']}?", False

def get_hint(state):
    """Возвращает подсказку для стандартного режима"""
    if state['hint_count'] >= state['max_hints']:
        return "Подсказки закончились."
        
    state['hint_count'] += 1
    hint_type = random.choice(['parity', 'half'])
    if hint_type == 'parity':
        if state['secret'] % 2 == 0:
            return "Подсказка: число чётное."
        else:
            return "Подсказка: число нечётное."
    else:  # half
        mid = (state['low'] + state['high']) // 2
        if state['secret'] <= mid:
            return "Подсказка: число в нижней половине диапазона."
        else:
            return "Подсказка: число в верхней половине диапазона."
        
def process_timed_guess(state, guess):
    elapsed = time.time() - state['start_time']
    if elapsed > state['time_limit']:
        state['game_over'] = True
        state['won'] = False
        return state, "Время вышло! Вы проиграли.", True
    new_state, msg, game_over = process_standard_guess(state, guess)
    return new_state, msg, game_over
    
    # Если время ещё есть, используем стандартную обработку
    new_state, msg, game_over = process_standard_guess(state, guess)
    return new_state, msg, game_over, False        

def check_timed_game(state):
    """Проверяет, не вышло ли время в режиме на время. Возвращает (game_over, message)"""
    if time.time() - state['start_time'] > state['time_limit']:
        return True, "Время вышло! Вы проиграли."
    return False, ""