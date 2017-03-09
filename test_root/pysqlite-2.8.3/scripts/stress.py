from pysqlite2 import dbapi2 as sqlite
import os, threading

def getcon():
    #con = sqlite.connect("db", isolation_level=None, timeout=5.0)
    con = sqlite.connect(":memory:")
    cur = con.cursor()
    cur.execute("create table test(i, s)")
    for i in range(10):
        cur.execute("insert into test(i, s) values (?, 'asfd')", (i,))
    con.commit()
    cur.close()
    return con

def reader(what):
    con = getcon()
    while 1:
        cur = con.cursor()
        cur.execute("select i, s from test where i % 1000=?", (what,))
        res = cur.fetchall()
        cur.close()
    con.close()

def appender():
    con = getcon()
    counter = 0
    while 1:
        cur = con.cursor()
        cur.execute("insert into test(i, s) values (?, ?)", (counter, "foosadfasfasfsfafs"))
        #cur.execute("insert into test(foo) values (?)", (counter,))
        counter += 1
        if counter % 100 == 0:
            #print "appender committing", counter
            con.commit()
        cur.close()
    con.close()


def updater():
    con = getcon()
    counter = 0
    while 1:
        cur = con.cursor()
        counter += 1
        if counter % 5 == 0:
            cur.execute("update test set s='foo' where i % 50=0")
            #print "updater committing", counter
            con.commit()
        cur.close()
    con.close()


def deleter():
    con = getcon()
    counter = 0
    while 1:
        cur = con.cursor()
        counter += 1
        if counter % 5 == 0:
            #print "deleter committing", counter
            cur.execute("delete from  test where i % 20=0")
            con.commit()
        cur.close()
    con.close()

threads = []

for i in range(10):
    continue
    threads.append(threading.Thread(target=lambda: reader(i)))

for i in range(5):
    threads.append(threading.Thread(target=appender))
    #threads.append(threading.Thread(target=updater))
    #threads.append(threading.Thread(target=deleter))

for t in threads:
    t.start()


