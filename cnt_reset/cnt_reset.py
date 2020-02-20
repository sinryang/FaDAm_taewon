import asyncio
import tornado.escape
import tornado.ioloop
import tornado.locks
import tornado.web
from tornado import gen
from tornado.tcpclient import TCPClient
import os.path
import uuid
import configparser

import psycopg2 as db

from datetime import datetime, timedelta
from tornado.options import define, options, parse_command_line

import time

def load_db_config():
    cwd = os.path.dirname(os.path.abspath(__file__))

    config = configparser.ConfigParser()
    config.read(os.path.join(cwd, 'config', 'config.ini'))

    return config['DATABASE']

config = load_db_config()

def reset():
    conn = db.connect(host= config['HOST'], dbname=config['DB_NAME'], user=config['USER'], password=config['PASSWORD'])
    cur = conn.cursor()

    reset_sql = 'ALTER SEQUENCE lvdt_data_date_cnt_seq RESTART WITH 1;'
    query_last_sql = "SELECT date FROM lvdt_data ORDER BY date DESC LIMIT 1"

    cur.execute(query_last_sql)

    rows = cur.fetchall()

    if (len(rows) == 1):
        print(rows[0][0].strftime("%Y-%m-%d"))
        if datetime.now().strftime("%Y-%m-%d") > rows[0][0].strftime("%Y-%m-%d"):
            print('run')
            cur.execute(reset_sql)
            conn.commit()

    cur.close()
    conn.close()

def main():
    parse_command_line()
    reset()
    tornado.ioloop.PeriodicCallback(reset, 200000).start()
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
