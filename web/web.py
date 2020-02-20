#!/usr/bin/env python3
#
# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import asyncio
import tornado.escape
import tornado.ioloop
import tornado.locks
import tornado.web
import os.path
import uuid
import configparser
import traceback

import psycopg2 as db

from datetime import datetime, timedelta
from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")

data_fields = {
    'lvdt_data' : ['data_id', 'date', 'date_cnt', 'axial', 'radial', 'data_stat', 'sensor_id'],
    'sensors' : ['id', 'ip', 'port', 'sensor_name', 'description', 'status'],
    'jointed_sensors': ['id', 'ip', 'port', 'sensor_name', 'description', 'status', 'axial', 'radial', 'data_stat']
}

numeric_fields = {
    'lvdt_data' : range(3, 5)
}

date_fields = {
    'lvdt_data' : 1
}

class DateException(Exception):
    """Exception for invalid date handleing"""
    pass

def load_db_config():
    cwd = os.path.dirname(os.path.abspath(__file__))

    config = configparser.ConfigParser()
    config.read(os.path.join(cwd, 'config', 'config.ini'))

    return config['DATABASE']

def convert_datetime_to_string(data, table_name='welding'):
    converted_data = []

    for row in data:
        new_data = list(row)
        new_data[date_fields[table_name]] = row[date_fields[table_name]].strftime("%Y-%m-%d %H:%M:%S")

        converted_data.append(new_data)

    return converted_data

def list_to_JSON_list(data, table_name='welding'):
    JSON_list = []

    for row in data:
        new_JSON = {}
        for i in range(len(data_fields[table_name])):
            new_JSON[data_fields[table_name][i]] = row[i]

        JSON_list.append(new_JSON)

    return JSON_list

def data_list_to_JSON_list(data):
    JSON_list = []

    for row in data:
        new_JSON = {}

        new_JSON['data_id'] = row[7] + str(row[0])
        new_JSON['date'] = row[1]
        new_JSON['date_cnt'] = row[2]
        new_JSON['axial'] = row[3]
        new_JSON['radial'] = row[4]
        new_JSON['data_stat'] = row[5]
        new_JSON['sensor_id'] = row[6]

        JSON_list.append(new_JSON)

    return JSON_list

def inc_str(_str):
    if _str == 'ZZ':
        return 'AA'

    if _str[-1] == 'Z':
        return chr(ord(_str[0]) + 1) + 'A'

    return _str[0] + chr(ord(_str[-1]) + 1)

config = load_db_config()

class ResetIdHandler(tornado.web.RequestHandler):
    def post(self):
        res = {
            'error': False,
            'msg': '',
            'data': ''
        }
        try:
            conn = db.connect(host= config['HOST'], dbname=config['DB_NAME'], user=config['USER'], password=config['PASSWORD'])
            cur = conn.cursor()

            reset_sql = 'ALTER SEQUENCE lvdt_data_data_id_seq RESTART WITH 1;'

            query_last_sql = "SELECT id_char FROM curr_id"

            cur.execute(query_last_sql)

            id_char = cur.fetchall()[0][0]
            print(id_char)
            id_char = inc_str(id_char)
            print(id_char)

            update_sql = "UPDATE curr_id SET id_char = '" + id_char + "' WHERE name = 'id_char'"
            print(update_sql)
            cur.execute(update_sql)
            cur.execute(reset_sql)
            conn.commit()

            cur.close()
            conn.close()

        except KeyError:
            res = {
                'error': True,
                'msg': 'Cannot find min_date or max_date. Check data.'
            }
            cur.close()
            conn.close()
        except TypeError:
            res = {
                'error': True,
                'msg': 'Type of dates should be string. Check the type.'
            }
            cur.close()
            conn.close()
        except ValueError:
            res = {
                'error': True,
                'msg': 'Invalid date format. The format should be %yyyy-%mm-%dd.'
            }
            cur.close()
            conn.close()
        except DateException as e:
            res = {
                'error': True,
                'msg': str(e)
            }
            cur.close()
            conn.close()

        except :
            cur.close()
            conn.close()
            tornado.web.HTTPError(500)

        self.write(tornado.escape.json_encode(res))


class DataRequestWithDateHandler(tornado.web.RequestHandler):
    def post(self):
        res = {
            'error': False,
            'msg': '',
            'data': ''
        }
        try:
            conn = db.connect(host= config['HOST'], dbname=config['DB_NAME'], user=config['USER'], password=config['PASSWORD'])
            cur = conn.cursor()

            body = tornado.escape.json_decode(self.request.body)

            table_name = body['table_name']
            min_date = body['min_date']
            max_date = body['max_date']
            print(min_date)
            print(max_date)

            d_min = datetime.strptime(min_date, '%Y-%m-%d')

            d_max = datetime.strptime(max_date, '%Y-%m-%d') + timedelta(days=1)

            if d_min > d_max:
                raise DateException('min_date should be equal or less than max_date.')

            sql = "SELECT * FROM " + table_name + " WHERE date > '" + d_min.strftime("%Y-%m-%d %H:%M:%S") + "' AND date < '" + d_max.strftime("%Y-%m-%d %H:%M:%S") + "'"

            cur.execute(sql)

            data = cur.fetchall()

            data = convert_datetime_to_string(data, table_name=table_name)

            JSON_list = data_list_to_JSON_list(data)


            res['data'] = JSON_list
            cur.close()
            conn.close()

        except Exception as e:
            traceback.print_tb(e.__traceback__)
            print(e)
            cur.close()
            conn.close()

        self.write(tornado.escape.json_encode(res))

class SensorLoadHandler(tornado.web.RequestHandler):
    def post(self):
        res = {
            'error': False,
            'msg': '',
            'data': ''
        }
        try:
            0
            conn = db.connect(host= config['HOST'], dbname=config['DB_NAME'], user=config['USER'], password=config['PASSWORD'])
            cur = conn.cursor()

            body = tornado.escape.json_decode(self.request.body)

            table_name = body['table_name']

            sql = "SELECT * FROM " + table_name

            cur.execute(sql)

            data = cur.fetchall()

            JSON_list = list_to_JSON_list(data, table_name=table_name)

            res['data'] = JSON_list
            cur.close()
            conn.close()

        except :
            cur.close()
            conn.close()
            tornado.web.HTTPError(500)

        self.write(tornado.escape.json_encode(res))

class SensorAddHandler(tornado.web.RequestHandler):
    def post(self):
        res = {
            'error': False,
            'msg': '',
            'data': ''
        }
        try:
            0
            conn = db.connect(host= config['HOST'], dbname=config['DB_NAME'], user=config['USER'], password=config['PASSWORD'])
            cur = conn.cursor()

            body = tornado.escape.json_decode(self.request.body)

            table_name = body['table_name']
            sensor_name = body['sensor_name']
            ip = body['ip']
            port = body['port']
            description = body['description']

            sql = "INSERT INTO " + table_name + " (ip, port, sensor_name, description) VALUES (%s, %s, %s, %s)"

            cur.execute(sql, (ip, port, sensor_name, description))
            conn.commit()

            JSON_list = list_to_JSON_list(data, table_name=table_name)

            res['data'] = JSON_list

            cur.close()
            conn.close()

        except :
            cur.close()
            conn.close()
            tornado.web.HTTPError(500)

        self.write(tornado.escape.json_encode(res))

class SensorEditHandler(tornado.web.RequestHandler):
    def post(self):
        res = {
            'error': False,
            'msg': '',
            'data': ''
        }

        try:
            0
            conn = db.connect(host= config['HOST'], dbname=config['DB_NAME'], user=config['USER'], password=config['PASSWORD'])
            cur = conn.cursor()

            body = tornado.escape.json_decode(self.request.body)

            table_name = body['table_name']
            sensor_id = body['id']
            sensor_name = body['sensor_name']
            ip = body['ip']
            port = body['port']
            description = body['description']

            sql = "UPDATE " + table_name + " SET ip = %s, port = %s, sensor_name = %s, description = %s WHERE id = %s"

            cur.execute(sql, (ip, port, sensor_name, description, sensor_id))
            conn.commit()

            JSON_list = list_to_JSON_list(data, table_name=table_name)

            res['data'] = JSON_list

            cur.close()
            conn.close()
        except :
            cur.close()
            conn.close()
            tornado.web.HTTPError(500)

        self.write(tornado.escape.json_encode(res))

class SensorDeleteHandler(tornado.web.RequestHandler):
    def post(self):
        res = {
            'error': False,
            'msg': '',
            'data': ''
        }

        try:
            0
            conn = db.connect(host= config['HOST'], dbname=config['DB_NAME'], user=config['USER'], password=config['PASSWORD'])
            cur = conn.cursor()

            body = tornado.escape.json_decode(self.request.body)

            table_name = body['table_name']
            sensor_id = body['id']

            sql = "DELETE FROM " + table_name + " WHERE id = %s"

            cur.execute(sql, (sensor_id,))
            conn.commit()

            JSON_list = list_to_JSON_list(data, table_name=table_name)

            res['data'] = JSON_list
            cur.close()
            conn.close()

        except :
            cur.close()
            conn.close()
            tornado.web.HTTPError(500)

        self.write(tornado.escape.json_encode(res))

class SensorStatusHandler(tornado.web.RequestHandler):
    def post(self):
        res = {
            'error': False,
            'msg': '',
            'data': ''
        }

        try:
            0
            conn = db.connect(host= config['HOST'], dbname=config['DB_NAME'], user=config['USER'], password=config['PASSWORD'])
            cur = conn.cursor()

            body = tornado.escape.json_decode(self.request.body)

            sensor_table_name = body['sensor_table_name']
            data_table_name = body['data_table_name']

            sensor_sql = "SELECT * FROM " + sensor_table_name

            cur.execute(sensor_sql)

            sensors = list(cur.fetchall())
            jointed_sensors = []


            for sensor in sensors:
                last_data_sql = "SELECT axial, radial, data_stat FROM " + data_table_name + " WHERE sensor_id = " + str(sensor[0]) + " ORDER BY data_id DESC LIMIT 1"
                cur.execute(last_data_sql)
                last_data = cur.fetchall()

                if (len(last_data) == 1):
                    jointed_sensors.append(sensor + last_data[0])
                else:
                    jointed_sensors.append(sensor + (0.0, 0.0, 0,))

            JSON_sensor_list = list_to_JSON_list(jointed_sensors, table_name='jointed_sensors')

            res['data'] = {'sensors':JSON_sensor_list}

            cur.close()
            conn.close()
        except :
            cur.close()
            conn.close()
            tornado.web.HTTPError(500)

        self.write(tornado.escape.json_encode(res))

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class DataSheetHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("data_sheet.html")

class DetailDataSheetHandler(tornado.web.RequestHandler):
    def post(self):
        process_id = self.get_argument('process_id', '')
        self.render("detail_data_sheet.html", process_id=process_id)

class DataSheetForExportHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("data_sheet_for_export.html")

class SensorManagementHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("sensor_management.html")

def main():
    parse_command_line()
    app = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/data/reset", ResetIdHandler),
            (r"/data_sheet/export", DataSheetForExportHandler),
            (r"/data/export", DataRequestWithDateHandler),
            (r"/sensor/management", SensorManagementHandler),
            (r"/sensor/load", SensorLoadHandler),
            (r"/sensor/add", SensorAddHandler),
            (r"/sensor/edit", SensorEditHandler),
            (r"/sensor/delete", SensorDeleteHandler),
            (r"/sensor/status", SensorStatusHandler),
        ],
        cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        xsrf_cookies=False,
        debug=options.debug,
    )
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()
