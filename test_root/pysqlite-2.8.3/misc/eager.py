from pysqlite2 import dbapi2 as sqlite3

Cursor = sqlite3.Cursor

class EagerCursor(Cursor):
    def __init__(self, con):
        Cursor.__init__(self, con)
        self.rows = []
        self.pos = 0

    def execute(self, *args):
        sqlite3.Cursor.execute(self, *args)
        self.rows = Cursor.fetchall(self)
        self.pos = 0

    def fetchone(self):
        try:
            row = self.rows[self.pos]
            self.pos += 1
            return row
        except IndexError:
            return None

    def fetchmany(self, num=None):
        if num is None:
            num = self.arraysize

        result = self.rows[self.pos:self.pos+num]
        self.pos += num
        return result

    def fetchall(self):
        result = self.rows[self.pos:]
        self.pos = len(self.rows)
        return result

def test():
    con = sqlite3.connect(":memory:")
    cur = con.cursor(EagerCursor)
    cur.execute("create table test(foo)")
    cur.executemany("insert into test(foo) values (?)", [(3,), (4,), (5,)])
    cur.execute("select * from test")
    print cur.fetchone()
    print cur.fetchone()
    print cur.fetchone()
    print cur.fetchone()
    print cur.fetchone()

if __name__ == "__main__":
    test()

