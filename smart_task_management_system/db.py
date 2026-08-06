"""
Database access layer.
All raw SQL for the app lives here so routes in app.py stay focused on
request/response logic. Uses PyMySQL with DictCursor so rows come back
as plain dictionaries (e.g. row['title']) instead of tuples.
"""
import pymysql
import pymysql.cursors
from config import Config


def get_db_connection():
    """Open a new connection to the MySQL database."""
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


# ---------------------------------------------------------------------------
# User queries
# ---------------------------------------------------------------------------

def get_user_by_username(conn, username):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        return cur.fetchone()


def get_user_by_email(conn, email):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        return cur.fetchone()


def get_user_by_id(conn, user_id):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        return cur.fetchone()


def create_user(conn, username, email, password_hash):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, password_hash),
        )
        return cur.lastrowid


# ---------------------------------------------------------------------------
# Task queries
# ---------------------------------------------------------------------------

def get_tasks_for_user(conn, user_id):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM tasks WHERE user_id = %s ORDER BY due_date IS NULL, due_date ASC",
            (user_id,),
        )
        return cur.fetchall()


def get_task_by_id(conn, task_id, user_id):
    """Fetch a task, scoped to the owning user so nobody can edit another
    user's task by guessing an id in the URL."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM tasks WHERE id = %s AND user_id = %s", (task_id, user_id)
        )
        return cur.fetchone()


def create_task(conn, user_id, title, description, due_date, priority):
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO tasks (user_id, title, description, due_date, priority, status)
               VALUES (%s, %s, %s, %s, %s, 'Pending')""",
            (user_id, title, description, due_date, priority),
        )
        return cur.lastrowid


def update_task(conn, task_id, user_id, title, description, due_date, priority):
    with conn.cursor() as cur:
        cur.execute(
            """UPDATE tasks SET title = %s, description = %s, due_date = %s, priority = %s
               WHERE id = %s AND user_id = %s""",
            (title, description, due_date, priority, task_id, user_id),
        )


def delete_task(conn, task_id, user_id):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM tasks WHERE id = %s AND user_id = %s", (task_id, user_id))


def toggle_task_status(conn, task_id, user_id):
    with conn.cursor() as cur:
        cur.execute(
            """UPDATE tasks
               SET status = IF(status = 'Completed', 'Pending', 'Completed')
               WHERE id = %s AND user_id = %s""",
            (task_id, user_id),
        )
