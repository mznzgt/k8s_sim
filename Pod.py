import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from request import Request
import threading

class Pod:
    def __init__(self, NAME, ASSIGNED_CPU, DEPLABEL, MSLABEL, HANDLINGTIME):
        # pod name
        self.podName = NAME
        # pod handling time
        self.handlingTime = HANDLINGTIME
        # pod assigned cpu
        self.assigned_cpu = ASSIGNED_CPU
        # pod available cpu
        self.available_cpu = ASSIGNED_CPU
        # pod deployment label
        self.deploymentLabel = DEPLABEL
        self.microserviceLabel = MSLABEL
        # pod staus by default if "pending"
        self.status = "PENDING"
        self.crash = threading.Event()
        # size of pod's pool = assigned cpu
        self.pool = ThreadPoolExecutor(max_workers=ASSIGNED_CPU)
        # list of request that the pod is deal with
        self.requests = []

    # method to be call when requests are in
    def HandleRequest(self, REQUEST):
        # each request create a thread
        def ThreadHandler():
            # -1 cpu when request first come
            self.available_cpu -=1
            # wait for the handling time to finish or crash
            self.crash.wait(timeout=(REQUEST.fail.wait(timeout=self.handlingTime)))
            # then cpu +1
            self.available_cpu +=1
            # if thread is crash, that means the request has fail
            if self.crash.is_set():
                REQUEST.fail.set()
        # incase there are too many request coming
        if len(self.requests) > (self.assigned_cpu * self.handlingTime):
            REQUEST.fail.set()
        # reqest list append the request in thread handler
        self.requests.append(self.pool.submit(ThreadHandler))
        # list of store active requests
        activeReqs = []
        # loop through requests's list
        for req in self.requests:
            # if request is not done
            if not req.done():
                # append it to the activeReqs list
                activeReqs.append(req)
        # pod.request = active requests that is not done
        self.requests = activeReqs