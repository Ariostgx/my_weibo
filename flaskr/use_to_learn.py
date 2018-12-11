
import sqlite3

conn = sqlite3.connect('test.db')
conn.row_factory = sqlite3.Row
print("Opened database successfully")
c = conn.cursor()
a = c.execute('''SELECT * FROM COMPANY''').fetchall()
b = c.execute('''SELECT * FROM factor''').fetchall()

print(a)
print(b)
print(c.lastrowid)
used_for_debug = 1

