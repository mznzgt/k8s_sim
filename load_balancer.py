from api_server import APIServer
import concurrent.futures
import time
import re

#LoadBalancer distributes requests to pods in Deployments
class LoadBalancer:
    def __init__(self, KIND, APISERVER, DEPLOYMENT):
        self.apiServer = APISERVER
        self.deployment = DEPLOYMENT
        self.running = True
        self.kind = KIND
        self.indexArray = []
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)

    def __call__(self):
        def ThreadHandler(req, serList):
            for ser in serList:
                # get all microservice for instruction file and send it to balance method
                ms=ser.replace('(','').replace(')','')
                self.balance(req,ms)
        # copy deployment's ms list
        self.indexArray = self.deployment.msList.copy()
        for i in range (0, len(self.indexArray)):
            self.indexArray[i] = 0
        while self.running:
            self.deployment.waiting.wait()
            with self.deployment.lock:
                # get deployment's pending requests and clear it
                requests = self.deployment.pendingReqs.copy()
                self.deployment.pendingReqs.clear()
                self.deployment.waiting.clear()
                for request in requests:
                    # bring pending requests to handled requests
                    self.deployment.handledReqs.append(request)
                    for ms in self.deployment.orderList:
                        parMSList = re.split("\+", ms)
                        while '' in parMSList: parMSList.remove('')
                        for par in parMSList:
                            serList = re.split("\.", par)
                            while '' in serList: serList.remove('')
                            # extract orderList's ms to handle requests
                            self.pool.submit(ThreadHandler(request, serList))
        self.pool.shutdown()

    # get port from endpoint and assign to the lowest utilization's one
    def balance(self, request, MS):
        with self.apiServer.etcdLock:
            endPoints = self.apiServer.GetEndPointsByLabel(self.deployment.deploymentLabel, MS)
            if len(endPoints) ==0:
                print('no endpoints found for '+self.deployment.deploymentLabel+' and microservice '+MS)
                request.fail.set()
                return
            # Utilization Aware load balancer
            endPoints.sort(key=lambda x:x.pod.available_cpu,reverse=True)
            pod = self.apiServer.GetPod(endPoints[0])
            pod.HandleRequest(request)