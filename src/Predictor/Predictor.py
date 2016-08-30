import pusher
import MySQLdb
import sys
import datetime
import logging
import threading
import time
from datetime import datetime as dt
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
    # connect
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
    # connect
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
                # You can show only the last error like this.
                # print cursor.messages[-1]
            else:
                print "\n".join(conn.messages)
                # Same here you can also do.
                # print self.db.messages[-1]
            conn.rollback()
    conn.close()
    return rows


def main():
    global adapter_pusher
    adapter_pusher = pusher.Pusher(
        app_id='231267',
        key='bf548749c8760edbe3b6',
        secret='6545a7b9465cde9fab73',
        ssl=True
    )

    while True:
        try:
            print "Predicting..."
            prediction_loop()

        except:
            app_log.info("Prediction Loop failed.\n")
            app_log.info(sys.exc_info())
            break


def prediction_loop():
    local_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    app_log.info("predicting for %s" % local_time)
    while True:
        try:
            sql("UPDATE stream SET intervention_id=%s WHERE user_id=%s", ("-1", "Not Logged In"))
            rows = sql_get("SELECT id,user_id,created_at,subjects "
                           "FROM stream WHERE intervention_id IS NULL AND local_time>=%s",
                           [local_time])
            for row in rows:
                row_id = row[0]
                collective_id = row[1]
                reminder_time = row[2]
                intervention = row[3]

                sql("UPDATE stream SET intervention_id=%s WHERE id=%s", ("Busy", row_id))
                threading.Thread(target=intervene, args=[row_id, collective_id, reminder_time, intervention]).start()
        except:
            app_log.info("Error: ")
            app_log.info(sys.exc_info())
            local_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            continue


def sleep_until(collective_id, reminder_time, using_timeout=False):
    if using_timeout is True:
        try:
            conn = MySQLdb.connect(host=cnf['host'], user=cnf['user'], passwd=cnf['password'], db='lassi')
            conn.autocommit(True)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM incentive_timeout")
            rows = cursor.fetchall()
            timeout = rows[0][0]
        except:
            timeout = 10  # default timeout

        time_diff = (dt.utcnow() - reminder_time).total_seconds() / 60  # in minutes
        wait_time = (timeout - int(round(time_diff))) * 60  # in seconds
    else:
        curr_timestamp = (dt.utcnow() - dt.fromtimestamp(0)).total_seconds()
        incentive_timestamp = (reminder_time - dt.fromtimestamp(0)).total_seconds()
        wait_time = incentive_timestamp - curr_timestamp
        print "%s\n%s\n%s\n" % (curr_timestamp, incentive_timestamp, wait_time)
        wait_time = int(round(wait_time))

    if wait_time > 0:
        app_log.info('timeout_for_collective(' + collective_id + ') for ' + str(wait_time) + ' seconds\n')
        time.sleep(wait_time)


def send_intervention_for_collective(collective_id, intervention):
    payload = {
        "project": "SmartSociety",
        "collective_id": collective_id,
        "intervention_type": "reminder",
        "intervention_text": intervention,
    }

    adapter_pusher.trigger('adapter', 'intervention', payload)
    app_log.info('send_intervention_for_collective(' + collective_id + '):' + str(payload) + '\n')


def intervene(row_id, collective_id, reminder_time, intervention):
    try:
        # sleep until it's time
        sleep_until(collective_id, reminder_time)
        # send intervention
        send_intervention_for_collective(collective_id, intervention)

        app_log.info("Collective:%s, intervention:%s" % (collective_id, intervention))
        sql("UPDATE stream SET intervention_id=%s WHERE id=%s", ("Sent", row_id))
        app_log.info("done execute\n")
    except:
        app_log.info("Error: ")
        app_log.info(sys.exc_info())
        sql("UPDATE stream SET intervention_id=%s WHERE id=%s", ("Failed", row_id))


if __name__ == "__main__":
    main()
