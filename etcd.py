from Pod import Pod
from deployment import Deployment
from end_point import EndPoint
from worker_node import WorkerNode
from concurrent.futures import ThreadPoolExecutor
import threading

class Etcd:
    def __init__(self):
        self.pendingPodList = []
        self.runningPodList = []
        self.deploymentList = []
        self.microserviceList = []
        self.microserviceTemplates = []
        self.nodeList = []
        self.endPointList = []
        self.reqCreator = ThreadPoolExecutor(max_workers=1)