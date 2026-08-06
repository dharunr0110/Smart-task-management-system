"""
Smart Task Management System
A Flask + MySQL web app for creating an account, logging in, and managing
personal tasks. Tasks are automatically grouped into Overdue / Due Today /
Upcoming / Completed based on their due date - that's the "smart" part.
"""
import re
import secrets
from datetime import date, datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
import db

app = Flask(__name__)
app.config.from_object(Config)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to continue.', 'error')
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    return dict(csrf_token=session['csrf_token'])


def csrf_valid():
    token = session.get('csrf_token')
    return token is not None and token == request.form.get('csrf_token')


def parse_due_date(value):
    """Convert an HTML <input type=date> string to a date object, or None."""
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


def clean_priority(value):
    return value if value in ('Low', 'Medium', 'High') else 'Medium'


def categorize_tasks(tasks):
    """Group tasks into smart buckets based on due date and status."""
    today = date.today()
    buckets = {'overdue': [], 'due_today': [], 'upcoming': [], 'completed': []}

    for task in tasks:
        if task['status'] == 'Completed':
            buckets['completed'].append(task)
            continue
        due = task['due_date']
        if due is None or due > today:
            buckets['upcoming'].append(task)
        elif due == today:
            buckets['due_today'].append(task)
        else:
            buckets['overdue'].append(task)

    return buckets


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        if not csrf_valid():
            flash('Your session expired, please try again.', 'error')
            return redirect(url_for('signup'))

        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = []
        if len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        if not EMAIL_RE.match(email):
            errors.append('Enter a valid email address.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        if password != confirm_password:
            errors.append('Passwords do not match.')

        if not errors:
            conn = db.get_db_connection()
            try:
                if db.get_user_by_username(conn, username):
                    errors.append('That username is already taken.')
                elif db.get_user_by_email(conn, email):
                    errors.append('An account with that email already exists.')
                else:
                    password_hash = generate_password_hash(password)
                    db.create_user(conn, username, email, password_hash)
                    flash('Account created. Please log in.', 'success')
                    return redirect(url_for('login'))
            finally:
                conn.close()

        for error in errors:
            flash(error, 'error')
        return render_template('signup.html', username=username, email=email)

    return render_template('signup.html', username='', email='')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        if not csrf_valid():
            flash('Your session expired, please try again.', 'error')
            return redirect(url_for('login'))

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        conn = db.get_db_connection()
        try:
            user = db.get_user_by_username(conn, username)
        finally:
            conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))

        flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


# ---------------------------------------------------------------------------
# Task routes
# ---------------------------------------------------------------------------

@app.route('/dashboard')
@login_required
def dashboard():
    conn = db.get_db_connection()
    try:
        tasks = db.get_tasks_for_user(conn, session['user_id'])
    finally:
        conn.close()

    buckets = categorize_tasks(tasks)
    counts = {key: len(value) for key, value in buckets.items()}
    return render_template('dashboard.html', buckets=buckets, counts=counts, today=date.today())


@app.route('/task/add', methods=['POST'])
@login_required
def add_task():
    if not csrf_valid():
        flash('Your session expired, please try again.', 'error')
        return redirect(url_for('dashboard'))

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    due_date = parse_due_date(request.form.get('due_date', ''))
    priority = clean_priority(request.form.get('priority', 'Medium'))

    if not title:
        flash('Task title is required.', 'error')
        return redirect(url_for('dashboard'))

    conn = db.get_db_connection()
    try:
        db.create_task(conn, session['user_id'], title, description, due_date, priority)
    finally:
        conn.close()

    flash('Task added.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/task/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    conn = db.get_db_connection()
    try:
        task = db.get_task_by_id(conn, task_id, session['user_id'])
        if not task:
            flash('Task not found.', 'error')
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            if not csrf_valid():
                flash('Your session expired, please try again.', 'error')
                return redirect(url_for('dashboard'))

            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            due_date = parse_due_date(request.form.get('due_date', ''))
            priority = clean_priority(request.form.get('priority', 'Medium'))

            if not title:
                flash('Task title is required.', 'error')
                return render_template('edit_task.html', task=task)

            db.update_task(conn, task_id, session['user_id'], title, description, due_date, priority)
            flash('Task updated.', 'success')
            return redirect(url_for('dashboard'))

        return render_template('edit_task.html', task=task)
    finally:
        conn.close()


@app.route('/task/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    if not csrf_valid():
        flash('Your session expired, please try again.', 'error')
        return redirect(url_for('dashboard'))

    conn = db.get_db_connection()
    try:
        db.delete_task(conn, task_id, session['user_id'])
    finally:
        conn.close()

    flash('Task deleted.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/task/toggle/<int:task_id>', methods=['POST'])
@login_required
def toggle_task(task_id):
    if not csrf_valid():
        flash('Your session expired, please try again.', 'error')
        return redirect(url_for('dashboard'))

    conn = db.get_db_connection()
    try:
        db.toggle_task_status(conn, task_id, session['user_id'])
    finally:
        conn.close()

    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
