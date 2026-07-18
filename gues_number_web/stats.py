import json
import os
import utils
import matplotlib.pyplot as plt

def get_stats_file(user):
    return os.path.join('data', f'stats_{user}.json')

def load_stats(user):
    file = get_stats_file(user)
    if not os.path.exists(file):
        return {'games': [], 'total': 0, 'wins': 0, 'best_attempts': None}
    with open(file, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_stats(user, stats):
    os.makedirs('data', exist_ok=True)
    with open(get_stats_file(user), 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=4, ensure_ascii=False)

def save_game_result(user, mode, difficulty, attempts, guesses, won):
    stats = load_stats(user)
    game_record = {
        'date': utils.current_timestamp(),
        'mode': mode,
        'difficulty': difficulty,
        'attempts': attempts,
        'guesses': guesses,
        'won': won
    }
    stats['games'].append(game_record)
    stats['total'] += 1
    if won:
        stats['wins'] += 1
    if won and (stats['best_attempts'] is None or attempts < stats['best_attempts']):
        stats['best_attempts'] = attempts
    save_stats(user, stats)

def show_stats(user):
    stats = load_stats(user)
    print(utils.colorize(f"\n=== Статистика пользователя {user} ===", 'cyan'))
    print(f"Всего игр: {stats['total']}")
    print(f"Побед: {stats['wins']}")
    if stats['total'] > 0:
        win_rate = stats['wins'] / stats['total'] * 100
        print(f"Процент побед: {win_rate:.1f}%")
    print(f"Лучший результат (минимальное число попыток): {stats['best_attempts']}")
    if stats['games']:
        print("\nПоследние игры:")
        for g in stats['games'][-5:]:
            print(f"{g['date']} - {g['mode']} - {g['difficulty']} - попыток: {g['attempts']} - {'победа' if g['won'] else 'поражение'}")

def export_stats_to_txt(user):
    """Сохраняет статистику пользователя в текстовый файл и возвращает имя файла"""
    stats = load_stats(user)
    filename = f"stats_{user}.txt"
    filepath = os.path.join('data', filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Статистика пользователя: {user}\n")
        f.write("=" * 40 + "\n")
        f.write(f"Всего игр: {stats['total']}\n")
        f.write(f"Побед: {stats['wins']}\n")
        if stats['total'] > 0:
            win_rate = stats['wins'] / stats['total'] * 100
            f.write(f"Процент побед: {win_rate:.1f}%\n")
        f.write(f"Лучший результат (мин. попыток): {stats['best_attempts']}\n")
        f.write("\nПоследние игры:\n")
        f.write("-" * 40 + "\n")
        for game in stats['games'][-10:]:
            f.write(f"{game['date']} | {game['mode']} | {game['difficulty']} | "
                    f"попыток: {game['attempts']} | {'победа' if game['won'] else 'поражение'}\n")
    
def plot_progress(user):
    """Строит график прогресса игрока и сохраняет в static/"""
    stats = load_stats(user)
    games = stats['games']
    if not games:
        return None
    # Берём последние 10 игр (или меньше, если игр мало)
    last_games = games[-10:]
    x = list(range(1, len(last_games) + 1))
    y = [g['attempts'] for g in last_games]
    
    plt.figure(figsize=(8, 4))
    plt.plot(x, y, marker='o', linestyle='-', color='#667eea', linewidth=2, markersize=8)
    plt.title(f'Прогресс игрока {user}', fontsize=14)
    plt.xlabel('Номер игры (последние 10)', fontsize=12)
    plt.ylabel('Количество попыток', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.xticks(x)
    
    # Сохраняем график
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    filename = f'progress_{user}.png'
    filepath = os.path.join(static_dir, filename)
    plt.savefig(filepath, bbox_inches='tight')
    plt.close()
    return filename