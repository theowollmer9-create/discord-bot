import sqlite3

conn = sqlite3.connect("stasi.db")
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS akten (
id INTEGER PRIMARY KEY AUTOINCREMENT,
roblox_user TEXT,
tat TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS kennzeichen (
id INTEGER PRIMARY KEY AUTOINCREMENT,
roblox_user TEXT,
kennzeichen TEXT,
fahrzeug TEXT
)""")

conn.commit()
