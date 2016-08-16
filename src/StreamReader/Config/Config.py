__author__ = 'eran'


class Config(object):
    conf = dict()

    # conf['clfFile'] ='/home/ise/Model/dismodel.pkl'
    conf['clfFile'] = '/home/shakedhi/Documents/Lassi/src/Algorithem/Model/dismodel.pkl'

    # conf['strmLog'] = '/home/ise/Logs/streamer.log'
    conf['strmLog'] = '/home/shakedhi/Documents/Logs/streamer.log'

    # conf['predLog'] = '/home/ise/Logs/predictor.log'
    conf['predLog'] = '/home/shakedhi/Documents/Logs/predictor.log'

    # conf['dis_predLog'] = '/home/ise/Logs/dis_predictor.log'
    conf['dis_predLog'] = '/home/shakedhi/Documents/Logs/dis_predictor.log'

    conf['debug'] = False

    conf['user'] = 'root'

    conf['password'] = '656544'

    conf['host'] = 'localhost'

    conf['db'] = 'streamer'

    conf['duration_dist'] = '/home/ise/Lassi/src/Predictor/session_duration_for_distribution.csv'
