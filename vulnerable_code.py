import os
import sqlite3

def dangerous_function(user_input):
    # Questa funzione dovrebbe far scattare l'allarme
    cmd = "echo " + user_input
    os.system(cmd) 

def get_user(name):
    # SQL Injection
    conn = sqlite3.connect("db.sqlite")
    sql = "SELECT * FROM users WHERE name = '" + name + "'"
    conn.execute(sql)