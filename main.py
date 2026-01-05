#!/usr/bin/env python3
"""
XTAGRAM - упрощенная социальная сеть
"""

from flask import Flask, request, redirect, render_template_string, session, jsonify
from datetime import datetime
import hashlib, os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Вместо базы данных используем простые структуры данных
users = {}
posts = []
comments = {}
likes = {}

# Простой счетчик для ID
user_counter = 1
post_counter = 1

# DEMO пользователь
users[1] = {
    'id': 1,
    'username': 'demo',
    'password': hashlib.sha256('demo'.encode()).hexdigest(),
    'avatar': 'https://i.pravatar.cc/100',
    'bio': 'Демо пользователь',
    'followers_count': 0,
    'following_count': 0
}

# HTML ШАБЛОН
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>XTAGRAM</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; font-family:-apple-system, sans-serif; }
        body { background:#fafafa; color:#262626; }
        .header { background:white; border-bottom:1px solid #dbdbdb; padding:12px 16px; display:flex; justify-content:space-between; align-items:center; }
        .logo { font-size:22px; font-weight:700; background:linear-gradient(45deg, #405de6, #833ab4, #fd1d1d); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
        .nav a { margin-left:20px; text-decoration:none; color:#262626; font-weight:500; }
        .container { max-width:600px; margin:20px auto; padding:0 16px; }
        .card { background:white; border:1px solid #dbdbdb; border-radius:12px; padding:16px; margin-bottom:16px; }
        .post-header { display:flex; align-items:center; margin-bottom:12px; }
        .avatar { width:32px; height:32px; border-radius:50%%; margin-right:12px; }
        .username { font-weight:600; }
        .time { color:#8e8e8e; font-size:14px; }
        .post-content { margin:12px 0; line-height:1.5; }
        .actions { display:flex; gap:16px; margin-top:12px; }
        .btn { padding:8px 16px; border-radius:8px; border:none; background:#0095f6; color:white; font-weight:600; cursor:pointer; }
        input, textarea { width:100%%; padding:12px; border:1px solid #dbdbdb; border-radius:8px; margin-bottom:12px; }
        @media (max-width:600px) { .container { padding:0 8px; } .nav a { margin-left:12px; } }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">XTAGRAM</div>
        <div class="nav">%s</div>
    </div>
    <div class="container">%s</div>
</body>
</html>
'''

def current_user():
    user_id = session.get('user_id')
    if user_id and user_id in users:
        return users[user_id]
    return None

def auth_required(f):
    def wrap(*a, **k):
        if not session.get('user_id'): 
            return redirect('/login')
        return f(*a, **k)
    wrap.__name__ = f.__name__
    return wrap

# ГЛАВНАЯ СТРАНИЦА - ОЧЕНЬ ПРОСТАЯ
@app.route('/')
def home():
    """Самый простой endpoint для health checks"""
    # Сначала проверяем, это health check запрос
    if request.args.get('health') == 'true' or \
       request.headers.get('User-Agent', '').startswith('kube') or \
       'health' in request.headers.get('User-Agent', '').lower():
        return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()}), 200
    
    user = current_user()
    
    if not user:
        # Неавторизованный пользователь - простая страница
        content = '''
            <div class="card" style="text-align:center;padding:40px;">
                <h1 style="margin-bottom:20px;">👋 XTAGRAM</h1>
                <p>Простая социальная сеть</p>
                <a href="/register" style="display:inline-block;margin-top:20px;" class="btn">Начать</a>
            </div>
        '''
        nav = '<a href="/login">Войти</a> <a href="/register">Регистрация</a>'
        return HTML % (nav, content)
    
    # Авторизованный пользователь - простая лента
    user_posts = [p for p in posts if p['user_id'] == user['id']][:5]
    
    posts_html = ''
    for p in user_posts:
        post_user = users.get(p['user_id'], {})
        posts_html += f'''
            <div class="card">
                <div class="post-header">
                    <img src="{post_user.get('avatar', '')}" class="avatar">
                    <div>
                        <div class="username">{post_user.get('username', 'User')}</div>
                        <div class="time">{p['time']}</div>
                    </div>
                </div>
                <div class="post-content">{p['content']}</div>
                <div class="actions">
                    <span>❤️ {p.get('likes', 0)}</span>
                </div>
            </div>
        '''
    
    nav = f'''
        <a href="/">🏠</a>
        <a href="/post">📝</a>
        <a href="/profile">👤</a>
        <a href="/logout">🚪</a>
    '''
    
    content = f'''
        <div class="card">
            <h3>Создать пост</h3>
            <form action="/post" method="POST">
                <textarea name="content" placeholder="Что нового?" rows="3" maxlength="200"></textarea>
                <button type="submit" class="btn">📤 Опубликовать</button>
            </form>
        </div>
        <h3>Ваши посты</h3>
        {posts_html if posts_html else '<div class="card"><p>У вас пока нет постов</p></div>'}
    '''
    
    return HTML % (nav, content)

@app.route('/health')
def health():
    """Явный health check endpoint"""
    return jsonify({'status': 'healthy', 'app': 'xtagram'}), 200

@app.route('/post', methods=['POST'])
@auth_required
def create_post():
    user = current_user()
    content = request.form.get('content', '').strip()
    
    if content and len(content) <= 200:
        global post_counter
        post = {
            'id': post_counter,
            'content': content,
            'user_id': user['id'],
            'likes': 0,
            'time': datetime.now().strftime('%d.%m.%Y %H:%M')
        }
        posts.append(post)
        post_counter += 1
    
    return redirect('/')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if username and password:
            global user_counter
            user_counter += 1
            
            users[user_counter] = {
                'id': user_counter,
                'username': username,
                'password': hashlib.sha256(password.encode()).hexdigest(),
                'avatar': f'https://i.pravatar.cc/100?u={username}',
                'bio': '',
                'followers_count': 0,
                'following_count': 0
            }
            
            session['user_id'] = user_counter
            return redirect('/')
    
    return HTML % ('<a href="/login">Войти</a>', 
                  '<div class="card"><h2>Регистрация</h2><form method="POST"><input name="username" placeholder="Имя" required><input type="password" name="password" placeholder="Пароль" required><button class="btn">Создать аккаунт</button></form></div>')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        for user_id, user in users.items():
            if user['username'] == username and user['password'] == hashlib.sha256(password.encode()).hexdigest():
                session['user_id'] = user_id
                return redirect('/')
        
        return 'Неверные данные'
    
    return HTML % ('<a href="/register">Регистрация</a>', 
                  '<div class="card"><h2>Вход</h2><form method="POST"><input name="username" placeholder="Имя" required><input type="password" name="password" placeholder="Пароль" required><button class="btn">Войти</button></form></div>')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

@app.route('/profile')
@auth_required
def profile():
    user = current_user()
    user_posts = [p for p in posts if p['user_id'] == user['id']]
    
    content = f'''
        <div class="card">
            <div style="text-align:center">
                <img src="{user['avatar']}" style="width:80px;height:80px;border-radius:50%;border:3px solid #405de6">
                <h2 style="margin-top:12px">{user['username']}</h2>
                {f'<p style="margin-top:8px;color:#666;">{user["bio"]}</p>' if user.get('bio') else ''}
                <div style="display:flex;justify-content:center;gap:32px;margin:20px 0">
                    <div><b>{len(user_posts)}</b><div>постов</div></div>
                    <div><b>{sum(p.get('likes', 0) for p in user_posts)}</b><div>лайков</div></div>
                </div>
            </div>
        </div>
        
        <h3>Посты</h3>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:4px;margin-top:16px;">
    '''
    
    # Добавляем несколько примеров изображений
    for i in range(min(9, len(user_posts) + 3)):
        content += f'<div style="background:#eee;aspect-ratio:1;border-radius:4px;"></div>'
    
    content += '</div>'
    
    nav = f'''
        <a href="/">🏠</a>
        <a href="/logout">🚪</a>
    '''
    
    return HTML % (nav, content)

if __name__ == '__main__':
    print("🚀 XTAGRAM запущен на http://0.0.0.0:5000")
    print("✅ Health check: / и /health")
    app.run(host='0.0.0.0', port=5000, debug=False)
