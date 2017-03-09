from __future__ import with_statement
from pysqlite2 import dbapi2 as sqlite3
from datetime import datetime, timedelta
import time

def read_modify_write():
    # Open connection and create example schema and data.
    # In reality, open a database file instead of an in-memory database.
    con = sqlite3.connect(":memory:")
    cur = con.cursor()
    cur.executescript("""
    create table test(id integer primary key, data);
    insert into test(data) values ('foo');
    insert into test(data) values ('bar');
    insert into test(data) values ('baz');
    """)

    # The read part. There are two ways for fetching data using pysqlite.
    # 1. "Lazy-reading"
    #    cur.execute("select ...")
    #    for row in cur:
    #       ...
    #
    #    Advantage: Low memory consumption, good for large resultsets, data is
    #    fetched on demand.
    #    Disadvantage: Database locked as long as you iterate over cursor.
    #
    # 2. "Eager reading"
    #   cur.fetchone() to fetch one row
    #   cur.fetchall() to fetch all rows
    #   Advantage: Locks cleared ASAP.
    #   Disadvantage: fetchall() may build large lists.

    cur.execute("select id, data from test where id=?", (2,))
    row = cur.fetchone()

    # Stupid way to modify the data column.
    lst = list(row)
    lst[1] = lst[1] + " & more"

    # This is the suggested recipe to modify data using pysqlite. We use
    # pysqlite's proprietary API to use the connection object as a context
    # manager.  This is equivalent to the following code:
    #
    # try:
    #     cur.execute("...")
    # except:
    #     con.rollback()
    #     raise
    # finally:
    #     con.commit()
    #
    # This makes sure locks are cleared - either by commiting or rolling back
    # the transaction.
    #
    # If the rollback happens because of concurrency issues, you just have to
    # try again until it succeeds.  Much more likely is that the rollback and
    # the raised exception happen because of other reasons, though (constraint
    # violation, etc.) - don't forget to roll back on errors.
    #
    # Or use this recipe. It's useful and gets everything done in two lines of
    # code.
    with con:
        cur.execute("update test set data=? where id=?", (lst[1], lst[0]))

def delete_older_than():
    # Use detect_types if you want to use date/time types in pysqlite.
    con = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_COLNAMES)
    cur = con.cursor()

    # With "DEFAULT current_timestamp" we have SQLite fill the timestamp column
    # automatically.
    cur.executescript("""
    create table test(id integer primary key, data, created timestamp default current_timestamp);
    """)
    with con:
        for i in range(3):
            cur.execute("insert into test(data) values ('foo')")
            time.sleep(1)

    # Delete older than certain interval
    # SQLite uses UTC time, so we need to create these timestamps in Python, too.
    with con:
        delete_before = datetime.utcnow() - timedelta(seconds=2)
        cur.execute("delete from test where created < ?", (delete_before,))

def modify_insert():
    # Use a unique index and the REPLACE command to have the "insert if not
    # there, but modify if it is there" pattern. Race conditions are taken care
    # of by transactions.
    con = sqlite3.connect(":memory:")
    cur = con.cursor()
    cur.executescript("""
    create table test(id integer primary key, name, age);
    insert into test(name, age) values ('Adam', 18);
    insert into test(name, age) values ('Eve', 21);
    create unique index idx_test_data_unique on test(name);
    """)

    with con:
        # Make Adam age 19
        cur.execute("replace into test(name, age) values ('Adam', 19)")

        # Create new entry
        cur.execute("replace into test(name, age) values ('Abel', 3)")

if __name__ == "__main__":
    read_modify_write()
    delete_older_than()
    modify_insert()
