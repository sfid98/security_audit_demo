import os
import sqlite3
from flask import request

AWS_ACCESS_KEY = "AKIA1234567890FAKEKEY" 
DB_PASSWORD = "admin_password_123!"

class UserManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def get_user_profile(self, username):
        """
        VULNERABILITY: SQL Injection
        Why: Concatenating strings directly into SQL query.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = f"SELECT * FROM users WHERE username = '{username}'"
        
        cursor.execute(query)
        return cursor.fetchall()

class SystemUtils:
    def check_server_status(self, ip_address):
        """
        VULNERABILITY: Command Injection
        Why: Passing unsanitized input to os.system.
        """
        command = "ping -c 1 " + ip_address
        os.system(command)

class FileServer:
    def read_log_file(self, filename):
        """
        VULNERABILITY: Path Traversal
        Why: No validation on filename.
        """
        base_dir = "/var/logs/"
        
        file_path = base_dir + filename
        
        with open(file_path, "r") as f:
            return f.read()

def api_handler():
    user_mgr = UserManager("users.db")
    user_mgr.get_user_profile(request.args.get("user"))

    utils = SystemUtils()
    utils.check_server_status(request.args.get("ip"))
