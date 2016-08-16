from Alg import IncentiveAlgorithm, getIncentiveID
import sched
import time
from apscheduler.schedulers.background import BackgroundScheduler

__author__ = 'dor'


class StupidAlg(IncentiveAlgorithm):
    def __init__(self, request):
        self.s = sched.scheduler(time.time, time.sleep)
        self.owner = request.user
        self.incentivesId = []
        self.usersId = []
        self.sched = BackgroundScheduler()

    def getAllIncentiveRagted(self, request):
        """
        return all the Incentives IDs in order by the top to the lowest
        :param request:GET
        :return:list of incentives IDs
        """
        return self.incentivesId

    @staticmethod
    def getIncentiveForUser(self, request, user_id):
        """
        Give the best Incentive for a specific user
        :param request: GET
        :param user_id: a user ID for the data Set
        :return: Incentive ID
        """
        return self.incentivesId[0]

    def getTheBestIncentive(self, request):
        """
        The Best Incentive for all the data set.
        what was the best of all.
        :param request: GET
        :return:Incentive ID
        """
        return self.incentivesId[0]

    def start(self, request, *args, **kwargs):
        """
        start the algorithm with giving incentives and Data Set
        :param request:POST
        :param args:
        :param kwargs:
        :return: Success if everything is working and Error if not
        """
        id_list = getIncentiveID(self, request.owner)
        self.incentivesId = sorted(id_list)

    def init(self, request):
        # self.sched.add_job(self.start(self,request), 'interval', minutes=2)
        self.sched.add_job(lambda: self.start(self, request), 'interval', id="start", name="start", minutes=60)
        self.start(self, request)
        self.sched = BackgroundScheduler.start(self.sched)

    def clear(self, request, *args, **kwargs):
        """
        clear all the information about this data set
        :return: Suceess
        """
        if request.user == self.owner:
            self.sched.remove_all_jobs()
            self.usersId = []
            self.incentivesId = []
