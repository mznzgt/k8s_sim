import threading
import re
from concurrent.futures import ThreadPoolExecutor

class Deployment:
    def __init__(self, INFOLIST):
        self.deploymentLabel = INFOLIST[0]
        self.msPath = INFOLIST[1]
        self.msList = []
        self.pendingReqs = []
        self.handledReqs = []
        self.waiting = threading.Event()
        self.lock = threading.Lock()
        self.pool = ThreadPoolExecutor(max_workers=25)
        self.orderList = []
        self.orderList = self.msPath.split(').(')