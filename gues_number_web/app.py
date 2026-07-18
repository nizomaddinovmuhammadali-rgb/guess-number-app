from flask import Flask, render_template, session, request, redirect, url_for
import auth
import game
import stats
import utils
import time
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        success, result = auth.authenticate(username, password)
        if success:
            session['user'] = result
            return redirect(url_for('game_menu'))
        else:
            return render_template('login.html', error=result)
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email', '')
        success, result = auth.register_user(username, password, email)
        if success:
            session['user'] = result
            return redirect(url_for('game_menu'))
        else:
            return render_template('register.html', error=result)
    return render_template('register.html')

@app.route('/game_menu')
def game_menu():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('game_menu.html', user=session['user'])

@app.route('/new_game', methods=['POST'])
def new_game():
    if 'user' not in session:
        return redirect(url_for('login'))

    mode = request.form['mode']
    difficulty = request.form['difficulty']

    if mode == 'standard':
        game_state = game.new_standard_game(difficulty)
    elif mode == 'reverse':
        game_state = game.new_reverse_game(difficulty)
    elif mode == 'timed':
        game_state = game.new_timed_game(difficulty)
    else:
        return "Неверный режим", 400

    session['game_state'] = game_state
    session['game_mode'] = mode

    return redirect(url_for('play'))

@app.route('/play', methods=['GET', 'POST'])
def play():
    if 'user' not in session or 'game_state' not in session:
        return redirect(url_for('game_menu'))

    game_state = session['game_state']
    message = session.pop('message', '')

    # Для режима на время вычисляем остаток времени
    if game_state['mode'] == 'timed':
        # Если start_time нет (например, при загрузке старого сохранения), создадим его
        if 'start_time' not in game_state:
            game_state['start_time'] = time.time()
        elapsed = time.time() - game_state['start_time']
        game_state['time_remaining'] = max(0, int(game_state['time_limit'] - elapsed))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'guess':
            try:
                guess = int(request.form['guess'])
            except ValueError:
                session['message'] = "Введите целое число."
                return redirect(url_for('play'))

            if game_state['mode'] == 'standard':
                new_state, msg, game_over = game.process_standard_guess(game_state, guess)
                session['game_state'] = new_state
                if game_over:
                    if session['user'] != 'guest':
                        stats.save_game_result(
                            session['user'],
                            'standard',
                            game_state['difficulty'],
                            new_state['attempts'],
                            new_state['guesses'],
                            won=new_state['won']
                        )
                    session.pop('game_state', None)
                    return render_template('game_over.html',
                                           message=msg,
                                           user=session['user'],
                                           won=new_state['won'],
                                           attempts=new_state['attempts'],
                                           mode=game_state['mode'],
                                           difficulty=game_state['difficulty'])
                else:
                    session['message'] = msg

            elif game_state['mode'] == 'timed':
                new_state, msg, game_over = game.process_timed_guess(game_state, guess)
                session['game_state'] = new_state
                if game_over:
                    if session['user'] != 'guest':
                        stats.save_game_result(
                            session['user'],
                            'timed',
                            game_state['difficulty'],
                            new_state['attempts'],
                            new_state['guesses'],
                            won=new_state['won']
                        )
                    session.pop('game_state', None)
                    return render_template('game_over.html',
                                           message=msg,
                                           user=session['user'],
                                           won=new_state['won'],
                                           attempts=new_state['attempts'],
                                           mode=game_state['mode'],
                                           difficulty=game_state['difficulty'])
                else:
                    session['message'] = msg

            else:
                session['message'] = "Этот режим пока не реализован."

        elif action == 'reverse_answer':
            answer = request.form['answer']
            new_state, msg, game_over = game.process_reverse_guess(game_state, answer)
            session['game_state'] = new_state
            if game_over:
                if session['user'] != 'guest':
                    stats.save_game_result(
                        session['user'],
                        'reverse',
                        game_state['difficulty'],
                        new_state['attempts'],
                        [],
                        won=new_state['won']
                    )
                session.pop('game_state', None)
                return render_template('game_over.html',
                                       message=msg,
                                       user=session['user'],
                                       won=new_state['won'],
                                       attempts=new_state['attempts'],
                                       mode=game_state['mode'],
                                       difficulty=game_state['difficulty'])
            else:
                session['message'] = msg

        elif action == 'hint':
            hint = game.get_hint(game_state)
            session['message'] = hint
            session['game_state'] = game_state

        elif action == 'save':
            if session['user'] == 'guest':
                session['message'] = "Гости не могут сохранять игру."
            else:
                mode = game_state['mode']
                difficulty = game_state['difficulty']
                attempts = game_state['attempts']
                low = game_state.get('low', 1)
                high = game_state.get('high', 100)
                hint_count = game_state.get('hint_count', 0)

                if mode == 'standard':
                    secret = game_state['secret']
                    guesses = game_state.get('guesses', [])
                    guess = None
                    start_time = None
                    time_limit = None
                elif mode == 'timed':
                    secret = game_state['secret']
                    guesses = game_state.get('guesses', [])
                    guess = None
                    start_time = game_state.get('start_time')
                    time_limit = game_state.get('time_limit')
                elif mode == 'reverse':
                    secret = 0
                    guesses = []
                    guess = game_state.get('guess')
                    start_time = None
                    time_limit = None
                else:
                    secret = 0
                    guesses = []
                    guess = None
                    start_time = None
                    time_limit = None

                filename = game.save_game(
                    session['user'],
                    mode,
                    difficulty,
                    secret,
                    attempts,
                    guesses,
                    low,
                    high,
                    hint_count,
                    guess,
                    start_time,
                    time_limit
                )
                session['message'] = f"Игра сохранена: {filename}"

        return redirect(url_for('play'))

    return render_template('play.html', game_state=game_state, message=message)

@app.route('/saves')
def saves_list():
    if 'user' not in session or session['user'] == 'guest':
        return redirect(url_for('game_menu'))
    user = session['user']
    saves = game.list_saves(user)
    save_files = [os.path.basename(f) for f in saves]
    return render_template('saves.html', saves=save_files, user=user)

@app.route('/load_save/<filename>')
def load_save(filename):
    if 'user' not in session or session['user'] == 'guest':
        return redirect(url_for('game_menu'))
    saves_dir = os.path.join('data', 'saves')
    filepath = os.path.join(saves_dir, filename)
    if not os.path.exists(filepath):
        return "Файл не найден", 404
    game_state = game.load_game(filepath)
    if game_state.get('user') != session['user']:
        return "Доступ запрещён", 403
    session['game_state'] = game_state
    session['game_mode'] = game_state['mode']
    session.pop('message', None)
    return redirect(url_for('play'))

@app.route('/stats')
def stats_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = session['user']
    if user == 'guest':
        return render_template('stats.html', user=user, stats=None, error="Гости не имеют статистики.", chart=None)
    user_stats = stats.load_stats(user)
    chart_file = stats.plot_progress(user) if user_stats['total'] > 0 else None
    return render_template('stats.html', user=user, stats=user_stats, error=None, chart=chart_file)

@app.route('/export_stats', methods=['POST'])
def export_stats():
    if 'user' not in session or session['user'] == 'guest':
        return redirect(url_for('stats_page'))
    user = session['user']
    filename = stats.export_stats_to_txt(user)
    return render_template('stats.html', user=user,
                           stats=stats.load_stats(user),
                           error=None,
                           export_message=f"Статистика экспортирована в файл {filename}")

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
