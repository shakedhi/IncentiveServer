import pusher
import MySQLdb
import sys
import datetime
import logging
import threading
import time
from logging.handlers import RotatingFileHandler
from Config import Config as MConf
from contextlib import closing

__author__ = 'eran'

cnf = MConf.Config().conf

log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

logFile = cnf['predLog']

my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=1 * 1024 * 1024, backupCount=50, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.INFO)

app_log = logging.getLogger('root')
app_log.setLevel(logging.INFO)
app_log.addHandler(my_handler)

adapter_pusher = None


def sql(query, params):
    """
    executes sql non query (i.e. insert, update, delete, etc.) with qiven parameters
    :param query: the query
    :param params: the parameters, corresponding to the query
    """
    conn = MySQLdb.connect(host=cnf['host'], user=cnf['user'], passwd=cnf['password'], db=cnf['db'])
    with closing(conn.cursor()) as cursor:
        try:
            cursor.execute(query, params)
            conn.commit()
        except MySQLdb.Error as e:
            app_log.info("Unable to connect to DB.\n")
            app_log.info(e)
            conn.rollback()
    conn.close()


def sql_get(query, params):
    """
    execute sql query (i.e. select) with qiven parameters
    :param query: the query
    :param params: the parameters, corresponding to the query
    :return: the sql query results or None if error occured.
    """
    conn = MySQLdb.connect(host=cnf['host'], user=cnf['user'], passwd=cnf['password'], db=cnf['db'])
    rows = None
    with closing(conn.cursor()) as cursor:
        try:
            cursor.execute(query, params)
            conn.commit()
            rows = cursor.fetchall()
        except MySQLdb.Error as e:
            app_log.info("Unable to connect to DB.\n")
            app_log.info(e)
            conn.rollback()
        except MySQLdb.ProgrammingError:
            if cursor:
                print "\n".join(conn.cursor().messages)
            else:
                print "\n".join(conn.messages)
            conn.rollback()
    conn.close()
    return rows


def sleep_timeout(user_id):
    """
    sleeps timeout minutes before sending intervention to user/collective with user_id
    :param user_id: the user/collective id
    """
    try:
        conn = MySQLdb.connect(host=cnf['host'], user=cnf['user'], passwd=cnf['password'], db='lassi')
        conn.autocommit(True)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM incentive_timeout")
        rows = cursor.fetchall()
        timeout = rows[0][0]
        conn.close()
    except:
        timeout = 10  # default timeout in minutes

    wait_time = timeout * 60  # timeout in seconds
    app_log.info('sleep_timeout(' + user_id + ') for ' + str(wait_time) + ' seconds\n')
    time.sleep(wait_time)


def get_invalidated_peers(collective_id):
    """
    gets a collective id and returns a list of peers that invalidated from
    the collective
    :param collective_id:
    :return: a list of peer ids
    """
    try:
        rows = sql_get("SELECT peer_id FROM invalidations WHERE collective_id=%s", [collective_id])
        rows = [x[0] for x in rows]
        sql("DELETE FROM invalidations WHERE collective_id=%s", [collective_id])
        return rows
    except:
        return []


def intervene(row_id, collective_id, intervention):
    """
    sends the intervention for the collective
    :param row_id: the row id in the database
    :param collective_id: the collective id
    :param intervention: the intervention msg/id
    """
    try:
        payload = {
            "project": "SmartSociety",
            "collective_id": collective_id,
            "intervention_type": "reminder",
            "intervention_text": intervention,
            "invalidated": get_invalidated_peers(collective_id)
        }

        adapter_pusher.trigger('adapter', 'intervention', payload)  # send intervention
        app_log.info('send_intervention_for_collective(' + collective_id + '):' + str(payload) + '\n')

        sql("UPDATE stream SET intervention_id=%s WHERE id=%s", ("Sent", row_id))
        app_log.info("done execute\n")
    except:
        app_log.info("Error: ")
        app_log.info(sys.exc_info())
        sql("UPDATE stream SET intervention_id=%s WHERE id=%s", ("Failed", row_id))


def prediction():
    """
    reads every 1 second the records from the streamer, and sends interventions to
    """
    try:
        local_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        rows = sql_get("SELECT id,user_id,data,intervention_id "
                       "FROM stream WHERE intervention_id IS NULL AND created_at<=%s", (local_time,))
        for row in rows:
            row_id = row[0]
            collective_id = row[1]
            intervention = row[2]
            intervention_id = row[3]

            if intervention_id is None:
                sql("UPDATE stream SET intervention_id=%s WHERE id=%s", ("Busy", row_id))
                threading.Thread(target=intervene, args=[row_id, collective_id, intervention]).start()
    except:
        app_log.info("Error: ")
        app_log.info(sys.exc_info())


def prediction_loop():
    prediction()
    threading.Timer(1, prediction_loop).start()  # loop each 1 second


if __name__ == "__main__":
    adapter_pusher = pusher.Pusher(
        app_id='231267',
        key='bf548749c8760edbe3b6',
        secret='6545a7b9465cde9fab73',
        ssl=True
    )

    try:
        print "Predicting..."
        prediction_loop()  # loop forever
        while True:
            time.sleep(60)
    except:
        print "Prediction stopped."
        exit(137)
