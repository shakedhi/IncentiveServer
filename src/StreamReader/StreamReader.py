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

log_file = cnf['strmLog']
my_handler = RotatingFileHandler(log_file, mode='a', maxBytes=1 * 1024 * 1024, backupCount=50, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.INFO)

app_log = logging.getLogger('root')
app_log.setLevel(logging.INFO)
app_log.addHandler(my_handler)


def sql(inc_type, user_id, user_type, city_name, country_name, project, data, created_at):
    """
    insert stream event data to the database
    :param inc_type: the type of the incentive (reminder, message or preconfigured)
    :param user_id: the user id
    :param user_type: the user type (either peer or collective)
    :param city_name: the city name
    :param country_name: the country name
    :param project: the project name
    :param data: the additional data
    :param created_at: the time which the event was created remotely
    """
    local_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    conn = MySQLdb.connect(host=cnf['host'], user=cnf['user'], passwd=cnf['password'], db=cnf['db'])
    cursor = conn.cursor()
    try:
        datet = parse(created_at)
        create_time = datetime.datetime(datet.year, datet.month, datet.day, datet.hour, datet.minute, datet.second)
        cursor.execute(
            "INSERT INTO stream (type,user_id,user_type,project,data,created_at,country_name,city_name,local_time) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (inc_type, user_id, user_type, project, data, create_time, country_name, city_name, local_time))
        conn.commit()
    except MySQLdb.Error as e:
        app_log.info(e)
        conn.rollback()
    conn.close()


def classification_callback(data):
    """
    invoked when a classification event was pushed
    :param data: the data recieved in the classification event
    """
    x = yaml.load(str(data))
    sql(x['type'], x['user_id'], x['user_type'], x['geo']['city_name'],
        x['geo']['country_name'], x['project'],  x['data'], x['created_at'])
    app_log.info("User:{0} Record added.\n".format(x['user_id']))


def connect_handler(data):
    """
    invoked when pusher is connected
    :param data: the data recieved in the connection event
    """
    channel = pusher.subscribe("ouroboros")
    channel.bind('classification', classification_callback)


if __name__ == "__main__":
    app_log.info("Starting Stream\n")

    while True:
        try:
            pusher = pusherclient.Pusher(key="bf548749c8760edbe3b6")
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
