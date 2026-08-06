"""
Application configuration.
Reads settings from environment variables (see .env.example).
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Used to sign session cookies and CSRF tokens - change this in production.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-this-in-production')

    # MySQL connection settings
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'smart_task_db')
