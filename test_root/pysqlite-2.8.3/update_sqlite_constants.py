import sqlite3

import urllib

FILENAME = "/tmp/toc.db"

stream = urllib.urlopen("https://sqlite.org/toc.db")
with open(FILENAME, "wb") as f:
    f.write(stream.read())

con = sqlite3.connect("/tmp/toc.db")
cur = con.cursor()
cur.execute("select name from toc where type='constant' and name not in ('SQLITE_SOURCE_ID', 'SQLITE_VERSION')")
with open("src/sqlite_constants.h", "w") as out:
    for row in cur:
        constant = row[0]
        out.write("#ifdef %s\n" % constant)
        out.write('{"%s", %s},\n' % (constant, constant))
        out.write("#endif\n")
