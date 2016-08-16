#!/usr/bin/env python

import sys
import time
import yaml
import pusherclient
import MySQLdb
import datetime
from dateutil.parser import parse
from Config import Config
import logging
from logging.handlers import RotatingFileHandler

sys.path.append('..')

log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
log_formatter.converter = time.gmtime
cnf = Config.Config().conf

root = logging.getLogger()
root.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
root.addHandler(ch)

pusher = None

logFile = cnf['strmLog']
my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=1 * 1024 * 1024, backupCount=50, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.INFO)

app_log = logging.getLogger('root')
app_log.setLevel(logging.INFO)
app_log.addHandler(my_handler)


def sql(user_id, city_name, country_name, project, subjects, created_at):
    local_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    # connect
    conn = MySQLdb.connect(host=cnf['host'], user=cnf['user'], passwd=cnf['password'], db=cnf['db'])

    cursor = conn.cursor()
    try:
        datet = parse(created_at)
        create_time = datetime.datetime(datet.year, datet.month, datet.day, datet.hour, datet.minute, datet.second)
        cursor.execute(
            "INSERT INTO stream (user_id,project,subjects,created_at,country_name,city_name,local_time) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (user_id, project, subjects, create_time, country_name, city_name, local_time))
        conn.commit()
    except MySQLdb.Error as e:
        app_log.info(e)
        conn.rollback()
    conn.close()


def channel_callback(data):
    x = yaml.load(str(data))

    if x['project'] == "smartcom":
        app_log.info("User:{0} Record added.\n".format(x['user_id']))
        sql(x['user_id'], x['geo']['city_name'], x['geo']['country_name'], x['project'], x['subjects'], x['created_at'])


def connect_handler(data):
    channel = pusher.subscribe("ouroboros")
    channel.bind('classification', channel_callback)


if __name__ == "__main__":
    global pusher
    app_log.info("Starting Stream\n")
    appkey = "bf548749c8760edbe3b6"

    while True:
        try:
            pusher = pusherclient.Pusher(appkey)
            pusher.connection.bind('pusher:connection_established', connect_handler)
            pusher.connect()

            time.sleep(3)
            while pusher.connection.state == "connected":
                time.sleep(3)

            app_log.info("pusher state is:" + pusher.connection.state + "\n")

        except KeyboardInterrupt:
            if pusher.connection.state == "connected":
                pusher.disconnect()
            break
        except:
            app_log.info("Stream Crashed\n")
            app_log.info(sys.exc_info())
            print sys.exc_info()
            continue

    app_log.info("Stream Closed\n")

