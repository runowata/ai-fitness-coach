# AI Fitness Coach - Flask Application
# -*- coding: utf-8 -*-

import os
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Flask & Extensions
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy

# AI Integration
import openai

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_TYPE'] = 'filesystem'

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    # Production (Render.com with PostgreSQL)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    # Development (SQLite)
    base_dir = Path(__file__).resolve().parent
    db_path = base_dir / "fitness_coach.db"
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
Session(app)

# AI Configuration
openai.api_key = os.getenv('OPENAI_API_KEY')

# =============================================================================
# MODELS (SQLAlchemy)
# =============================================================================

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Hash in production!
    
    # Profile data
    age = db.Column(db.Integer)
    timezone = db.Column(db.String(50), default='Europe/Zurich')
    archetype = db.Column(db.String(20))  # bro, sergeant, intellectual
    
    # Gamification
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    streak_days = db.Column(db.Integer, default=0)
    total_workouts = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_workout_at = db.Column(db.DateTime)
    
    # Relationships
    workouts = db.relationship('Workout', backref='user', lazy=True)
    achievements = db.relationship('UserAchievement', backref='user', lazy=True)
    
    def add_xp(self, points):
        """Add XP and calculate new level"""
        self.xp += points
        self.level = (self.xp // 100) + 1
        db.session.commit()
    
    def __repr__(self):
        return f"<User {self.username}>"

class Exercise(db.Model):
    __tablename__ = 'exercises'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    muscle_groups = db.Column(db.Text)  # JSON string
    difficulty = db.Column(db.String(20))  # beginner, intermediate, advanced
    equipment = db.Column(db.String(50))
    
    def __repr__(self):
        return f"<Exercise {self.name}>"

class WorkoutPlan(db.Model):
    __tablename__ = 'workout_plans'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    plan_data = db.Column(db.Text)  # JSON string with plan details
    duration_weeks = db.Column(db.Integer, default=4)
    current_week = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<WorkoutPlan {self.title}>"

class Workout(db.Model):
    __tablename__ = 'workouts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    workout_data = db.Column(db.Text)  # JSON string with exercises
    video_playlist = db.Column(db.Text)  # JSON string with video URLs
    is_completed = db.Column(db.Boolean, default=False)
    completion_time = db.Column(db.DateTime)
    feedback = db.Column(db.Text)  # JSON string with emoji feedback
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Workout {self.date} for {self.user_id}>"

class Achievement(db.Model):
    __tablename__ = 'achievements'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    trigger_type = db.Column(db.String(20))  # workout_count, streak_days, xp_earned
    trigger_value = db.Column(db.Integer)
    xp_reward = db.Column(db.Integer)
    badge_icon = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f"<Achievement {self.name}>"

class UserAchievement(db.Model):
    __tablename__ = 'user_achievements'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    achievement_id = db.Column(db.String(36), db.ForeignKey('achievements.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserAchievement {self.user_id}:{self.achievement_id}>"

class Story(db.Model):
    __tablename__ = 'stories'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text)  # Story content
    cover_image = db.Column(db.String(500))
    unlock_achievement_id = db.Column(db.String(36), db.ForeignKey('achievements.id'))
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f"<Story {self.title}>"

# =============================================================================
# ROUTES
# =============================================================================

@app.route('/')
def home():
    return render_template('simple/home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Validation
        if not username or not email or not password:
            flash('Все поля обязательны', 'error')
            return render_template('simple/register.html')
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует', 'error')
            return render_template('simple/register.html')
        
        # Create user
        user = User(
            username=username,
            email=email,
            password=password  # TODO: Hash password in production!
        )
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        flash('Регистрация успешна!', 'success')
        return redirect(url_for('onboarding'))
    
    return render_template('simple/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        
        flash('Неверный email или пароль', 'error')
    
    return render_template('simple/login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route('/onboarding')
def onboarding():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Simple questions for MVP
    questions = [
        {
            'id': 'goal',
            'question': 'Какая ваша основная цель?',
            'options': ['Похудение', 'Набор мышечной массы', 'Улучшение здоровья', 'Выносливость']
        },
        {
            'id': 'frequency',
            'question': 'Как часто вы тренируетесь?',
            'options': ['Никогда', '1-2 раза в неделю', '3-4 раза в неделю', 'Каждый день']
        },
        {
            'id': 'limitations',
            'question': 'Есть ли у вас ограничения?',
            'options': ['Нет', 'Проблемы со спиной', 'Травмы коленей', 'Другие проблемы']
        }
    ]
    
    return render_template('simple/onboarding.html', questions=questions)

@app.route('/onboarding/submit', methods=['POST'])
def onboarding_submit():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # Get answers
    answers = {
        'goal': request.form.get('goal'),
        'frequency': request.form.get('frequency'),
        'limitations': request.form.get('limitations'),
        'archetype': request.form.get('archetype', 'bro')
    }
    
    # Update user profile
    user.archetype = answers['archetype']
    
    # Generate workout plan
    workout_plan = generate_workout_plan(user, answers)
    
    # Save workout plan
    plan = WorkoutPlan(
        user_id=user.id,
        title=f"Персональный план для {user.username}",
        description="AI-сгенерированный план тренировок",
        plan_data=json.dumps(answers)
    )
    db.session.add(plan)
    db.session.commit()
    
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    recent_workouts = Workout.query.filter_by(user_id=user.id).order_by(Workout.date.desc()).limit(5).all()
    
    stats = {
        'total_workouts': user.total_workouts,
        'current_streak': user.streak_days,
        'xp': user.xp,
        'level': user.level
    }
    
    return render_template('simple/dashboard.html', user=user, stats=stats, workouts=recent_workouts)

@app.route('/workout')
def workout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # Create today's workout
    today_workout = {
        'exercises': [
            {'name': 'Отжимания', 'sets': 3, 'reps': '10-15', 'rest': '60 сек'},
            {'name': 'Приседания', 'sets': 3, 'reps': '15-20', 'rest': '60 сек'},
            {'name': 'Планка', 'sets': 3, 'reps': '30-60 сек', 'rest': '45 сек'}
        ],
        'videos': generate_video_playlist(user.archetype or 'bro'),
        'motivation': get_motivation_message(user.archetype or 'bro')
    }
    
    return render_template('simple/workout.html', workout=today_workout, user=user)

@app.route('/workout/complete', methods=['POST'])
def complete_workout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # Get feedback
    feedback = {
        'difficulty': request.form.get('difficulty'),
        'enjoyment': request.form.get('enjoyment'),
        'energy': request.form.get('energy')
    }
    
    # Create workout record
    workout = Workout(
        user_id=user.id,
        date=datetime.now().date(),
        workout_data=json.dumps(request.form.to_dict()),
        feedback=json.dumps(feedback),
        is_completed=True,
        completion_time=datetime.utcnow()
    )
    db.session.add(workout)
    
    # Update user stats
    user.total_workouts += 1
    user.last_workout_at = datetime.utcnow()
    user.add_xp(50)  # Base XP for completing workout
    
    # Update streak
    yesterday = datetime.now().date() - timedelta(days=1)
    if user.last_workout_at and user.last_workout_at.date() == yesterday:
        user.streak_days += 1
    else:
        user.streak_days = 1
    
    db.session.commit()
    
    # Check achievements
    check_achievements(user)
    
    flash('Тренировка завершена! +50 XP', 'success')
    return redirect(url_for('dashboard'))

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_workout_plan(user, answers):
    """Generate workout plan using OpenAI"""
    if not openai.api_key:
        return "Базовый план тренировок (OpenAI API не настроен)"
    
    try:
        prompt = f"""
        Создай персональный план тренировок для пользователя:
        Цель: {answers['goal']}
        Частота: {answers['frequency']}
        Ограничения: {answers['limitations']}
        Архетип тренера: {answers['archetype']}
        
        Ответь в формате JSON с планом на неделю.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Базовый план тренировок (ошибка AI: {str(e)})"

def generate_video_playlist(archetype):
    """Generate video playlist based on archetype"""
    base_videos = [
        {'type': 'technique', 'title': 'Техника отжиманий', 'url': '/static/videos/pushups_technique.mp4'},
        {'type': 'technique', 'title': 'Техника приседаний', 'url': '/static/videos/squats_technique.mp4'},
    ]
    
    # Add archetype-specific motivational videos
    if archetype == 'bro':
        base_videos.append({
            'type': 'motivation', 
            'title': 'Мотивация от братана', 
            'url': '/static/videos/bro_motivation.mp4'
        })
    elif archetype == 'sergeant':
        base_videos.append({
            'type': 'motivation', 
            'title': 'Приказ сержанта', 
            'url': '/static/videos/sergeant_motivation.mp4'
        })
    elif archetype == 'intellectual':
        base_videos.append({
            'type': 'motivation', 
            'title': 'Научный подход', 
            'url': '/static/videos/intellectual_motivation.mp4'
        })
    
    return base_videos

def get_motivation_message(archetype):
    """Get motivation message based on archetype"""
    messages = {
        'bro': "Давай, братан! Покажи на что способен! 💪",
        'sergeant': "Рота, подъем! Время показать силу и дисциплину! 🎖️",
        'intellectual': "Каждое повторение - это инвестиция в ваше здоровье. Начнем! 🧠"
    }
    return messages.get(archetype, messages['bro'])

def check_achievements(user):
    """Check and award achievements"""
    # Simple achievement checking
    achievements_to_check = [
        {'name': 'Первая тренировка', 'trigger': 'workout_count', 'value': 1, 'xp': 100},
        {'name': 'Неделя тренировок', 'trigger': 'streak_days', 'value': 7, 'xp': 200},
        {'name': '10 тренировок', 'trigger': 'workout_count', 'value': 10, 'xp': 500},
    ]
    
    for ach_data in achievements_to_check:
        # Check if user qualifies and hasn't earned this yet
        if ach_data['trigger'] == 'workout_count' and user.total_workouts >= ach_data['value']:
            # Check if not already earned
            existing = UserAchievement.query.join(Achievement).filter(
                UserAchievement.user_id == user.id,
                Achievement.name == ach_data['name']
            ).first()
            
            if not existing:
                # Create achievement if it doesn't exist
                achievement = Achievement.query.filter_by(name=ach_data['name']).first()
                if not achievement:
                    achievement = Achievement(
                        name=ach_data['name'],
                        description=f"Достижение: {ach_data['name']}",
                        trigger_type=ach_data['trigger'],
                        trigger_value=ach_data['value'],
                        xp_reward=ach_data['xp'],
                        badge_icon='🏆'
                    )
                    db.session.add(achievement)
                    db.session.commit()
                
                # Award achievement
                user_achievement = UserAchievement(
                    user_id=user.id,
                    achievement_id=achievement.id
                )
                db.session.add(user_achievement)
                user.add_xp(ach_data['xp'])
                
                flash(f'Новое достижение: {ach_data["name"]}! +{ach_data["xp"]} XP', 'achievement')

# =============================================================================
# API ROUTES
# =============================================================================

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok',
        'users_count': User.query.count(),
        'workouts_count': Workout.query.count()
    })

# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

def init_db_tables():
    """Initialize database tables and sample data"""
    with app.app_context():
        db.create_all()
        
        # Create sample exercises if none exist
        if Exercise.query.count() == 0:
            exercises = [
                Exercise(name='Отжимания', slug='pushups', description='Классические отжимания', difficulty='beginner'),
                Exercise(name='Приседания', slug='squats', description='Приседания с собственным весом', difficulty='beginner'),
                Exercise(name='Планка', slug='plank', description='Статическое упражнение для кора', difficulty='beginner'),
                Exercise(name='Подтягивания', slug='pullups', description='Подтягивания на перекладине', difficulty='intermediate'),
            ]
            for exercise in exercises:
                db.session.add(exercise)
            
            db.session.commit()
            print("✅ Sample exercises created")
        
        print("✅ Database initialized successfully")

if __name__ == '__main__':
    init_db_tables()
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))