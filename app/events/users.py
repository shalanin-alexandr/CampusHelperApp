import json
import hashlib

USERS_FILE = "users.json"


def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate(username, password):
    users = load_users()
    hashed = hash_password(password)
    for user in users:
        if user["username"] == username and user["password"] == hashed:
            return user["role"]
    return None


def add_user(username, password, role="user"):
    users = load_users()
    if any(u["username"] == username for u in users):
        print("⚠️ Пользователь уже существует.")
        return
    users.append({
        "username": username,
        "password": hash_password(password),
        "role": role
    })
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)
    print(f"✅ Пользователь {username} добавлен с ролью {role}")
