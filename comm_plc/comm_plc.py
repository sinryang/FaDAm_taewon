import traceback
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

data_fields = {
    'lvdt_data' : ['data_id', 'date', 'date_cnt', 'axial', 'radial', 'data_stat', 'sensor_id'],
    'sensors' : ['id', 'ip', 'port', 'sensor_name', 'description', 'status'],
    'jointed_sensors': ['id', 'ip', 'port', 'sensor_name', 'description', 'status', 'axial', 'radial']
}

data_stats = ['None', 'OK', 'NG']

t0 = time.time()


req_data_msg = '500000FF03FF000018000A04010000D*0000000015'
write_msg = '500000FF03FF00002C000A14010000D*00000B0001'

def foo():
    print(time.time() - t0)

def load_db_config():
    cwd = os.path.dirname(os.path.abspath(__file__))

    config = configparser.ConfigParser()
    config.read(os.path.join(cwd, 'config', 'config.ini'))

    return config['DATABASE']

def list_to_JSON_list(data, table_name='welding'):
    JSON_list = []

    for row in data:
        new_JSON = {}
        for i in range(len(data_fields[table_name])):
            new_JSON[data_fields[table_name][i]] = row[i]

        JSON_list.append(new_JSON)

    return JSON_list

config = load_db_config()

@gen.coroutine
def monitor_sensor(sensor, config):
    print(sensor)
    update_sql = "UPDATE sensors SET status = %s WHERE id = %s"
    query_last_sql = "SELECT axial, radial FROM lvdt_data ORDER BY date DESC LIMIT 1"
    query_curr_id_sql = "SELECT id_char FROM curr_id"
    insert_sql = "INSERT INTO lvdt_data (date,axial,radial,data_stat,sensor_id, id_char) VALUES (%s, %s, %s, %s, %s, %s)"

    try:
        stream = yield TCPClient().connect(sensor['ip'], sensor['port'], timeout=200)
        print(req_data_msg)
        yield stream.write((req_data_msg).encode())
        reply = yield stream.read_bytes(80)
        print(reply)
        msg = reply.decode().strip()

        D0 = msg[22:26]
        D1 = int(msg[26:30], 16) / 1000.0
        D2 = msg[30:34]
        D3 = int(msg[34:38], 16) / 1000.0
        D4 = int(msg[38:42], 16)
        D5 = int(msg[42:46], 16)
        D10= int(msg[62:66], 16)

        yield stream.write((write_msg + D0).encode())
        stream.close()

        conn = db.connect(host= config['HOST'], dbname=config['DB_NAME'], user=config['USER'], password=config['PASSWORD'])
        cur = conn.cursor()

        cur.execute(query_curr_id_sql)
        id_char = cur.fetchall()[0][0]

        cur.execute(query_last_sql)
        rows = cur.fetchall()

        if len(rows) == 0:
            cur.execute(insert_sql, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), D1, D3, data_stats[D10], sensor['id'], id_char))
            conn.commit()
        else:
            axial = rows[0][0]
            radial = rows[0][1]

            if D1 != axial and D3 != radial:
                cur.execute(insert_sql, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), D1, D3, data_stats[D10], sensor['id'], id_char))
                conn.commit()

        cur.execute(update_sql, ('running', sensor['id']))
        conn.commit()

        cur.close()
        conn.close()
        stream.close()

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        print(e)
        stream.close()
        cur.close()
        conn.close()




def monitor_sensors():
    conn = db.connect(host= config['HOST'], dbname=config['DB_NAME'], user=config['USER'], password=config['PASSWORD'])
    cur = conn.cursor()

    foo()

    sql = "SELECT * FROM sensors"

    cur.execute(sql)

    sensors = list_to_JSON_list(cur.fetchall(), table_name='sensors')

    cur.close()
    conn.close()

    for sensor in sensors:
        monitor_sensor(sensor, config)



def main():
    parse_command_line()
    tornado.ioloop.PeriodicCallback(monitor_sensors, 2000).start()
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
