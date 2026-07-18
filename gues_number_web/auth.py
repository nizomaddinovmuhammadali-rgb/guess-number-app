import json
import hashlib
import os
from utils import current_timestamp

DATA_DIR = 'data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_users(users):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

def register_user(username, password, email=''):
    """Возвращает (True, username) или (False, сообщение об ошибке)"""
    users = load_users()
    if username in users:
        return False, "Пользователь с таким именем уже существует."
    users[username] = {
        'password': hash_password(password),
        'email': email,
        'created': current_timestamp()
    }
    save_users(users)
    return True, username

def authenticate(username, password):
    """Возвращает (True, username) или (False, сообщение)"""
    users = load_users()
    if username in users and users[username]['password'] == hash_password(password):
        return True, username
    return False, "Неверное имя пользователя или пароль."