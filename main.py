#!/usr/bin/env python3
"""
XTAGRAM - полная соцсеть с Android уведомлениями
"""

from flask import Flask, request, redirect, render_template_string, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib, os, json, time

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///xtagram.db'
db = SQLAlchemy(app)

# МОДЕЛИ
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(64))
    avatar = db.Column(db.String(200), default="https://i.pravatar.cc/100")

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    user_id = db.Column(db.Integer)
    likes = db.Column(db.Integer, default=0)
    time = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    title = db.Column(db.String(100))
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    time = db.Column(db.DateTime, default=datetime.utcnow)

# ХЕЛПЕРЫ
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
def current_user(): return User.query.get(session.get('user_id', 0))
def auth_required(f):
    def wrap(*a, **k):
        if not session.get('user_id'): return redirect('/login')
        return f(*a, **k)
    wrap.__name__ = f.__name__
    return wrap

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
        .btn-secondary { background:#efefef; color:black; }
        input, textarea { width:100%%; padding:12px; border:1px solid #dbdbdb; border-radius:8px; margin-bottom:12px; }
        .android-badge { background:#4CAF50; color:white; padding:4px 8px; border-radius:12px; font-size:12px; margin-left:10px; }
        .notification-bell { position:relative; }
        .notification-count { position:absolute; top:-8px; right:-8px; background:red; color:white; border-radius:50%%; width:20px; height:20px; display:flex; align-items:center; justify-content:center; font-size:12px; }
        @media (max-width:600px) { .container { padding:0 8px; } .nav a { margin-left:12px; } }
    </style>
    <script>
        // ANDROID УВЕДОМЛЕНИЯ
        let isAndroid = false;
        
        // Определяем Android
        function detectAndroid() {
            if (typeof Android !== 'undefined') {
                isAndroid = true;
                console.log('📱 В Android приложении');
                document.body.classList.add('android-app');
                return true;
            }
            
            if (navigator.userAgent.includes('XTAGRAM-App')) {
                isAndroid = true;
                console.log('📱 В WebView Android');
                return true;
            }
            
            return false;
        }
        
        // Отправка уведомления
        function sendAndroidNotification(title, message) {
            if (!isAndroid) return false;
            
            try {
                if (typeof Android !== 'undefined') {
                    Android.showNotification(title, message);
                    console.log('✅ Уведомление отправлено в Android');
                    return true;
                }
            } catch (e) {
                console.error('Ошибка Android:', e);
            }
            return false;
        }
        
        // При загрузке страницы
        document.addEventListener('DOMContentLoaded', function() {
            isAndroid = detectAndroid();
            
            // Показываем статус
            if (isAndroid) {
                const status = document.createElement('div');
                status.className = 'card';
                status.innerHTML = '<div style="display:flex;align-items:center;gap:10px;"><span style="font-size:24px;">📱</span><div><b>Android приложение</b><br><small>Уведомления включены</small></div></div>';
                document.querySelector('.container').prepend(status);
            }
            
            // Перехватываем создание постов
            document.querySelectorAll('form').forEach(form => {
                if (form.action.includes('post') || form.querySelector('textarea')) {
                    form.addEventListener('submit', function(e) {
                        const textarea = this.querySelector('textarea');
                        if (textarea && textarea.value.trim()) {
                            const content = textarea.value;
                            
                            // Отправляем уведомление
                            sendAndroidNotification(
                                'Новый пост в XTAGRAM',
                                content.substring(0, 100) + (content.length > 100 ? '...' : '')
                            );
                            
                            // Вибрация
                            if (navigator.vibrate) navigator.vibrate(200);
                            
                            // Отправляем на сервер для логирования
                            fetch('/api/log_notification', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({
                                    type: 'new_post',
                                    content: content.substring(0, 50)
                                })
                            });
                        }
                    });
                }
            });
            
            // Кнопка теста уведомлений
            const testBtn = document.createElement('button');
            testBtn.className = 'btn-secondary';
            testBtn.style.marginTop = '10px';
            testBtn.innerHTML = '🔔 Тест уведомления';
            testBtn.onclick = function() {
                if (sendAndroidNotification('Тест XTAGRAM', 'Уведомления работают!')) {
                    alert('✅ Уведомление отправлено в Android!');
                } else {
                    alert('⚠️  Не в Android приложении');
                }
            };
            
            // Добавляем кнопку в форму создания поста
            const form = document.querySelector('form');
            if (form) form.appendChild(testBtn);
        });
    </script>
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

# РОУТЫ
@app.route('/')
def home():
    user = current_user()
    if user:
        posts = Post.query.order_by(Post.time.desc()).limit(20).all()
        posts_html = ''.join([f'''
            <div class="card">
                <div class="post-header">
                    <img src="{User.query.get(p.user_id).avatar}" class="avatar">
                    <div>
                        <div class="username">{User.query.get(p.user_id).username}</div>
                        <div class="time">{p.time.strftime('%%d.%%m.%%Y %%H:%%M')}</div>
                    </div>
                </div>
                <div class="post-content">{p.content}</div>
                <div class="actions">
                    <button onclick="like({p.id})" class="btn">❤️ {p.likes}</button>
                    <button onclick="comment({p.id})" class="btn-secondary">💬</button>
                    <button onclick="sharePost({p.id})" class="btn-secondary">↪️</button>
                </div>
            </div>''' for p in posts])
        
        # Уведомления пользователя
        notifications = Notification.query.filter_by(user_id=user.id, is_read=False).count()
        nav = f'''
            <a href="/" class="notification-bell">🏠{f"<span class='notification-count'>{notifications}</span>" if notifications > 0 else ""}</a>
            <a href="/post">📝</a>
            <a href="/messages">💬</a>
            <a href="/profile">👤</a>
            <a href="/logout">🚪</a>
        '''
        
        content = f'''
            <div class="card">
                <h3>Создать пост</h3>
                <form action="/post" method="POST">
                    <textarea name="content" placeholder="Что нового?" rows="3"></textarea>
                    <button type="submit" class="btn">📤 Опубликовать</button>
                </form>
            </div>
            {posts_html}
            <script>
                function like(id){fetch("/like/"+id).then(r=>r.json()).then(data=>{alert('Лайк добавлен!');location.reload();})}
                function sharePost(id){sendAndroidNotification("Поделились постом", "ID: "+id)}
            </script>
        '''
        
        return HTML % (nav, content)
    
    return HTML % ('<a href="/login">Войти</a> <a href="/register">Регистрация</a>', 
                  '<div class="card" style="text-align:center;padding:40px;"><h1 style="margin-bottom:20px;">👋 XTAGRAM</h1><p>Социальная сеть с Android уведомлениями</p><a href="/register" style="display:inline-block;margin-top:20px;" class="btn">Начать</a></div>')

@app.route('/api/log_notification', methods=['POST'])
@auth_required
def log_notification():
    """Логирование уведомлений"""
    data = request.json
    user = current_user()
    
    notification = Notification(
        user_id=user.id,
        title='Android Notification',
        message=data.get('type', 'unknown') + ': ' + data.get('content', ''),
        is_read=False
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({'status': 'logged'})

@app.route('/post', methods=['POST'])
@auth_required
def create_post():
    """Создание поста с уведомлением"""
    content = request.form['content']
    user = current_user()
    
    # Создаем пост
    post = Post(content=content, user_id=user.id)
    db.session.add(post)
    db.session.commit()
    
    # Логируем уведомление
    notification = Notification(
        user_id=user.id,
        title='Новый пост создан',
        message=f'Вы создали пост: {content[:50]}...',
        is_read=False
    )
    db.session.add(notification)
    db.session.commit()
    
    # Отправляем уведомления подписчикам
    all_users = User.query.filter(User.id != user.id).all()
    for u in all_users:
        notif = Notification(
            user_id=u.id,
            title=f'Новый пост от {user.username}',
            message=content[:100] + ('...' if len(content) > 100 else ''),
            is_read=False
        )
        db.session.add(notif)
    
    db.session.commit()
    
    return redirect('/')

@app.route('/notifications')
@auth_required
def notifications():
    """Страница уведомлений"""
    user = current_user()
    notifs = Notification.query.filter_by(user_id=user.id).order_by(Notification.time.desc()).limit(50).all()
    
    notifs_html = ''.join([f'''
        <div class="card" style="border-left:4px solid {"#405de6" if not n.is_read else "#ccc"}">
            <div style="display:flex;justify-content:space-between;">
                <div><b>{n.title}</b></div>
                <small class="time">{n.time.strftime("%%H:%%M")}</small>
            </div>
            <div style="margin-top:8px;">{n.message}</div>
            {f'<a href="/read_notification/{n.id}" style="font-size:12px;color:#405de6;">Отметить прочитанным</a>' if not n.is_read else ''}
        </div>
    ''' for n in notifs])
    
    return HTML % (
        '<a href="/">🏠</a> <a href="/logout">🚪</a>',
        f'<h2>🔔 Уведомления</h2>{notifs_html if notifs else "<p>Нет уведомлений</p>"}'
    )

@app.route('/read_notification/<int:notif_id>')
@auth_required
def read_notification(notif_id):
    """Отметить уведомление как прочитанное"""
    notif = Notification.query.get(notif_id)
    if notif and notif.user_id == current_user().id:
        notif.is_read = True
        db.session.commit()
    return redirect('/notifications')

# Остальные роуты (регистрация, логин, профиль и т.д.) остаются как в оригинале
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        u = User(username=request.form['username'], password=hash_pw(request.form['password']))
        db.session.add(u); db.session.commit()
        session['user_id'] = u.id
        return redirect('/')
    return HTML % ('<a href="/login">Войти</a>', 
                  '<div class="card"><h2>Регистрация</h2><form method="POST"><input name="username" placeholder="Имя пользователя"><input type="password" name="password" placeholder="Пароль"><button class="btn">Создать аккаунт</button></form></div>')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form['username'], password=hash_pw(request.form['password'])).first()
        if u: session['user_id'] = u.id; return redirect('/')
        return 'Неверные данные'
    return HTML % ('<a href="/register">Регистрация</a>', 
                  '<div class="card"><h2>Вход</h2><form method="POST"><input name="username" placeholder="Имя"><input type="password" name="password" placeholder="Пароль"><button class="btn">Войти</button></form></div>')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

@app.route('/profile')
@auth_required
def profile():
    u = current_user()
    posts = Post.query.filter_by(user_id=u.id).all()
    grid = '<div class="grid" style="display:grid;grid-template-columns:repeat(3,1fr);gap:4px;margin-top:16px;">' + ''.join([f'<img src="https://picsum.photos/400/400?random={i}" style="width:100%;aspect-ratio:1;object-fit:cover;border-radius:4px;">' for i in range(9)]) + '</div>'
    return HTML % ('<a href="/">🏠</a> <a href="/logout">🚪</a>', 
                  f'<div class="card"><div style="text-align:center"><img src="{u.avatar}" style="width:80px;height:80px;border-radius:50%;border:3px solid #405de6"><h2 style="margin-top:12px">{u.username}</h2><div style="display:flex;justify-content:center;gap:32px;margin:20px 0"><div><b>{len(posts)}</b><div>постов</div></div><div><b>{sum(p.likes for p in posts)}</b><div>лайков</div></div></div></div>{grid}</div>')

# ЗАПУСК
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.first():
            u = User(username='demo', password=hash_pw('demo'))
            db.session.add(u); db.session.commit()
    app.run(host='0.0.0.0', port=5000, debug=True)
