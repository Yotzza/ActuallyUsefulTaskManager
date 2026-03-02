import re
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task_manager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    created_tasks = db.relationship('Task', foreign_keys='Task.created_by', backref='creator', lazy=True)
    claimed_tasks = db.relationship('Task', foreign_keys='Task.claimed_by', backref='claimer', lazy=True)
    room_memberships = db.relationship('RoomMember', backref='user', lazy=True)
    owned_rooms = db.relationship('Room', backref='owner', lazy=True)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    unique_code = db.Column(db.String(10), unique=True, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    members = db.relationship('RoomMember', backref='room', lazy=True, cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='room', lazy=True, cascade='all, delete-orphan')

class RoomMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='Tasks')  # Tasks, In Progress, Finished
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    claimed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    claimed_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)

# Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    user_rooms = [rm.room for rm in user.room_memberships]
    owned_rooms = user.owned_rooms
    
    return render_template('index.html', user=user, user_rooms=user_rooms, owned_rooms=owned_rooms)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash('Login sucessful! Welcome!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        
        # Validacija username-a
        if not validate_username(username):
            flash('Username must be at least 3 characters and can contain numbers and characters', 'error')
            return render_template('register.html')
        
        # Validacija email-a
        if not validate_email(email):
            flash('Enter valid email', 'error')
            return render_template('register.html')
        
        # Provera da li username već postoji
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        # Provera da li email već postoji
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('register.html')
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Successfully registered! You can now login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Successfully logged out', 'success')
    return redirect(url_for('login'))

@app.route('/create_room', methods=['POST'])
def create_room():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    room_name = request.form['room_name']
    unique_code = generate_unique_code()
    
    room = Room(
        name=room_name,
        unique_code=unique_code,
        owner_id=session['user_id']
    )
    db.session.add(room)
    db.session.commit()
    
    # Add owner as member
    member = RoomMember(room_id=room.id, user_id=session['user_id'])
    db.session.add(member)
    db.session.commit()
    
    flash(f'Room "{room_name}" is created! Code: {unique_code}', 'success')
    return redirect(url_for('index'))

@app.route('/join_room', methods=['POST'])
def join_room():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    room_code = request.form['room_code']
    room = Room.query.filter_by(unique_code=room_code).first()
    
    if not room:
        flash('Room with this code does not exist', 'error')
        return redirect(url_for('index'))
    
    # Check if already member
    existing_member = RoomMember.query.filter_by(room_id=room.id, user_id=session['user_id']).first()
    if existing_member:
        flash('You are already a member of this room', 'error')
        return redirect(url_for('index'))
    
    # Add as member
    member = RoomMember(room_id=room.id, user_id=session['user_id'])
    db.session.add(member)
    db.session.commit()
    
    flash(f'Successfully joined room "{room.name}"!', 'success')
    return redirect(url_for('room', room_id=room.id))

@app.route('/room/<int:room_id>')
def room(room_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    room = Room.query.get_or_404(room_id)
    user = User.query.get(session['user_id'])
    
    # Check if user is member
    is_member = RoomMember.query.filter_by(room_id=room_id, user_id=session['user_id']).first()
    if not is_member:
        flash('Nemate pristup ovoj sobi', 'error')
        return redirect(url_for('index'))
    
    # Get tasks by status
    tasks = Task.query.filter_by(room_id=room_id).all()
    tasks_dict = {
        'Tasks': [t for t in tasks if t.status == 'Tasks'],
        'In Progress': [t for t in tasks if t.status == 'In Progress'],
        'Finished': [t for t in tasks if t.status == 'Finished']
    }
    
    return render_template('room.html', room=room, tasks_dict=tasks_dict, user=user, is_owner=room.owner_id == session['user_id'])

@app.route('/delete_room', methods=['POST'])
def delete_room():
    if 'user_id' not in session:
        return jsonify({'error': 'You are not logged in'}), 401
    
    room_id = request.form['room_id']
    room = Room.query.get_or_404(room_id)
    
    # Check if user is owner
    if room.owner_id != session['user_id']:
        return jsonify({'error': 'Only owner can delete room'}), 403
    
    # Delete room (cascade will delete tasks and members)
    db.session.delete(room)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/add_task', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return jsonify({'error': 'You are not logged in'}), 401
    
    room_id = request.form['room_id']
    title = request.form['title']
    description = request.form.get('description', '')
    
    # Check if user is member
    is_member = RoomMember.query.filter_by(room_id=room_id, user_id=session['user_id']).first()
    if not is_member:
        return jsonify({'error': 'You dont have access to this room'}), 403
    
    task = Task(
        title=title,
        description=description,
        created_by=session['user_id'],
        room_id=room_id
    )
    db.session.add(task)
    db.session.commit()
    
    return jsonify({'success': True, 'task_id': task.id})

@app.route('/claim_task', methods=['POST'])
def claim_task():
    if 'user_id' not in session:
        return jsonify({'error': 'You are not logged in'}), 401
    
    task_id = request.form['task_id']
    task = Task.query.get_or_404(task_id)
    
    # Check if user is member of the room
    is_member = RoomMember.query.filter_by(room_id=task.room_id, user_id=session['user_id']).first()
    if not is_member:
        return jsonify({'error': 'You dont have access to this room'}), 403
    
    if task.status != 'Tasks':
        return jsonify({'error': 'Task cannot be claimed'}), 400
    
    task.status = 'In Progress'
    task.claimed_by = session['user_id']
    task.claimed_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/cancel_task', methods=['POST'])
def cancel_task():
    if 'user_id' not in session:
        return jsonify({'error': 'You are not logged in'}), 401
    
    task_id = request.form['task_id']
    task = Task.query.get_or_404(task_id)
    
    # Check if user is member of the room
    is_member = RoomMember.query.filter_by(room_id=task.room_id, user_id=session['user_id']).first()
    if not is_member:
        return jsonify({'error': 'You dont have access to this room'}), 403
    
    # Check if user is the one who claimed the task
    if task.claimed_by != session['user_id']:
        return jsonify({'error': 'Only user who claimed the task can cancel it'}), 403
    
    # Reset task to Tasks status
    task.status = 'Tasks'
    task.claimed_by = None
    task.claimed_at = None
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/complete_task', methods=['POST'])
def complete_task():
    if 'user_id' not in session:
        return jsonify({'error': 'You are not logged in'}), 401
    
    task_id = request.form['task_id']
    task = Task.query.get_or_404(task_id)
    
    # Check if user is member of the room
    is_member = RoomMember.query.filter_by(room_id=task.room_id, user_id=session['user_id']).first()
    if not is_member:
        return jsonify({'error': 'You dont have access to this room'}), 403
    
    if task.status != 'In Progress':
        return jsonify({'error': 'Task cannot be finished'}), 400
    
    task.status = 'Finished'
    task.completed_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/delete_task', methods=['POST'])
def delete_task():
    if 'user_id' not in session:
        return jsonify({'error': 'You are not logged in'}), 401
    
    task_id = request.form['task_id']
    task = Task.query.get_or_404(task_id)
    
    # Check if user is owner of the room
    room = Room.query.get(task.room_id)
    if room.owner_id != session['user_id']:
        return jsonify({'error': 'Only owner of the room can delete tasks'}), 403
    
    db.session.delete(task)
    db.session.commit()
    
    return jsonify({'success': True})

def generate_unique_code():
    while True:
        code = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(6))
        if not Room.query.filter_by(unique_code=code).first():
            return code

def validate_username(username):
    """Validira username - dozvoljava samo slova i brojeve"""
    if not username or len(username) < 3 or len(username) > 80:
        return False
    # Dozvoljava samo: slova (a-z, A-Z) i brojeve (0-9)
    pattern = r'^[a-zA-Z0-9]+$'
    return re.match(pattern, username) is not None

def validate_email(email):
    """Validira email - osnovna email validacija"""
    if not email or len(email) > 120:
        return False
    # Jednostavna email validacija - dozvoljava brojeve u email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def init_db():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
