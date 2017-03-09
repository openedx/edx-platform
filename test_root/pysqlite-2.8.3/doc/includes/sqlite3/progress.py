from pysqlite2 import dbapi2 as sqlite3

def progress():
    print "Query still executing. Please wait ..."

con = sqlite3.connect(":memory:")
con.execute("create table test(x)")

# Let's create some data
con.executemany("insert into test(x) values (?)", [(x,) for x in xrange(300)])

# A progress handler, executed every 10 million opcodes
con.set_progress_handler(progress, 10000000)

# A particularly long-running query
killer_stament = """
    select count(*) from (
        select t1.x from test t1, test t2, test t3
    )
    """

con.execute(killer_stament)
print "-" * 50

# Clear the progress handler
con.set_progress_handler(None, 0)

con.execute(killer_stament)

