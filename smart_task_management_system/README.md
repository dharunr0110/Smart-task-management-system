# Smart Task Management System

A Flask + MySQL web app for creating an account, logging in, and managing
personal tasks. Tasks are automatically grouped into **Overdue**, **Due
Today**, **Upcoming**, and **Completed** based on their due date - that's
the "smart" part.

## Features

- User signup and login (passwords hashed with Werkzeug's PBKDF2, never
  stored in plain text)
- Session-based authentication with a login-required guard on every
  task route
- Create, read, update, delete tasks (title, description, due date,
  priority)
- Mark a task complete / back to pending with one click
- Dashboard automatically sorts tasks into Overdue / Due Today /
  Upcoming / Completed sections
- CSRF protection on every form submission
- Each user only ever sees and edits their own tasks

## Tech stack

- **Backend:** Python 3, Flask
- **Database:** MySQL (via PyMySQL)
- **Frontend:** Server-rendered Jinja2 templates, vanilla CSS/JS (no
  frontend build step required)

## Project structure

```
smart_task_management_system/
├── app.py              # Routes and request handling
├── db.py                # All SQL queries
├── config.py             # Reads settings from environment variables
├── schema.sql             # MySQL table definitions
├── requirements.txt        # Python dependencies
├── .env.example             # Copy to .env and fill in your MySQL credentials
├── static/
│   ├── css/style.css
│   └── js/app.js
└── templates/
    ├── base.html
    ├── login.html
    ├── signup.html
    ├── dashboard.html
    └── edit_task.html
```

## Setup

### 1. Install MySQL

Make sure a MySQL server is installed and running locally, and that you
know the root (or another) user's password.

### 2. Create the database

```bash
mysql -u root -p < schema.sql
```

This creates the `smart_task_db` database along with the `users` and
`tasks` tables.

### 3. Create a virtual environment and install dependencies

```bash
cd smart_task_management_system
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Then open `.env` and set `MYSQL_PASSWORD` (and `MYSQL_USER` /
`MYSQL_DB` if different from the defaults) to match your MySQL setup.
Also change `SECRET_KEY` to any random string.

### 5. Run the app

```bash
python app.py
```

Visit **http://127.0.0.1:5000** in your browser. Sign up for an
account, log in, and start adding tasks.

## Troubleshooting

- **`pymysql.err.OperationalError: (1045, "Access denied for user...")`**
  Your `MYSQL_USER` / `MYSQL_PASSWORD` in `.env` don't match a real
  MySQL account. Double-check them.
- **`pymysql.err.OperationalError: (2003, "Can't connect to MySQL server...")`**
  MySQL isn't running, or `MYSQL_HOST` / `MYSQL_PORT` in `.env` are
  wrong.
- **`Unknown database 'smart_task_db'`**
  Run step 2 (`mysql -u root -p < schema.sql`) before starting the app.
