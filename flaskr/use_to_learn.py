"""
import sqlite3
def dict_factory(cursor, row):
    d = {}
    for index, col in enumerate(cursor.description):
        d[col[0]] = row[index]
    return d

conn = sqlite3.connect(r'test.db')
conn.row_factory = dict_factory
print("Opened database successfully")
c = conn.cursor()
a = c.execute('''SELECT * FROM COMPANY''').fetchone()
print(a)
used_for_debug = 1
"""


s = '//@asd: wqewqeqwe //@zxc: wqewqeqwe //@qwe: wqewqeqwe //@jkl: wqewqeqwe'
x = s.rfind('123')
print(x)
print(s[:x])
