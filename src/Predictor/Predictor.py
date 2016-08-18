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


def tmprint(txt):
    local_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    print "{0} - {1}".format(local_time, txt)


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
            print ("Ready")
            prediction_loop()
        except:
            app_log.info("Prediction Loop failed.\n")
            app_log.info(sys.exc_info())
            continue


def prediction_loop():
    local_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    app_log.info("predicting for %s" % local_time)
    while True:
        try:
            sql("UPDATE stream SET intervention_id=%s WHERE user_id=%s", ("-1", "Not Logged In"))
            rows = sql_get("SELECT id,user_id,local_time FROM stream WHERE intervention_id IS NULL AND local_time>=%s",
                           [local_time])
            if len(rows) == 0:
                continue
            for row in rows:
                row_id = row[0]
                collective_id = row[1]
                arrival_time = row[2]
                sql("UPDATE stream SET intervention_id=%s WHERE id=%s", ("Busy", row_id))
                threading.Thread(target=intervene, args=[row_id, collective_id, arrival_time]).start()
        except:
            app_log.info("Error2: ")
            app_log.info(sys.exc_info())
            local_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            continue


def current_timeout():
    try:
        conn = MySQLdb.connect(host=cnf['host'], user=cnf['user'], passwd=cnf['password'], db='lassi')
        conn.autocommit(True)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM incentive_timeout')
        rows = cursor.fetchall()
        initial_value = rows[0][0]
    except:
        initial_value = 10
    return initial_value


def intervene(row_id, collective_id, arrival_time):
    try:
        timeout = current_timeout()
        app_log.info('timeout_for_collective(' + collective_id + ') for ' + str(timeout) + ' seconds\n')

        curr_time = datetime.datetime.utcnow()
        time_diff = (curr_time - arrival_time).total_seconds() / 60
        time_diff = round(time_diff, 0)
        if time_diff < timeout:
            time.sleep(timeout - time_diff)

        intervention_id = send_intervention_for_collective(collective_id)

        app_log.info("Collective:%s, intervention_id:%s" % (collective_id, intervention_id))
        sql("UPDATE stream SET intervention_id=%s WHERE id=%s", (intervention_id, row_id))
        app_log.info("done execute\n")
    except:
        app_log.info("Error: ")
        app_log.info(sys.exc_info())
        sql("UPDATE stream SET intervention_id=%s WHERE id=%s", ("Failed", row_id))


def send_intervention_for_collective(collective_id):
    payload = {
        "project": "smartcom",
        "collective_id": collective_id,
        "intervention_type": "reminder",
        "intervention_text": "please return",
    }

    adapter_pusher.trigger('adapter', 'intervention', payload)
    app_log.info('send_intervention_for_collective(' + collective_id + '):' + str(payload) + '\n')

    intervention_id = 1  # TODO: fix hard coded intervention
    app_log.info('SUCCESS send_intervention_for_collective(' + collective_id + '):' + str(intervention_id))
    return intervention_id


if __name__ == "__main__":
    # import pdb
    # pdb.set_trace()
    main()
