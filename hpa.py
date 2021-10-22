import threading
import time
import math

class HPA:
    def __init__(self, APISERVER, LOOPTIME, INFOLIST):
        self.apiServer = APISERVER
        self.running = True
        self.time = LOOPTIME
        self.deploymentLabel = INFOLIST[0]
        self.setPoint = float(INFOLIST[1]) / 100
        self.maxReps = 5
        self.minReps = 1

    def __call__(self):
        while self.running:
            with self.apiServer.etcdLock:
                # get the given deployment
                deployment = self.apiServer.GetDepByLabel(self.deploymentLabel)
                # if not ms assciated with the deployment
                if deployment == None:
                    self.running = False
                    break
                # loop through each ms in the deployment
                for ms in deployment.msList:
                    microservice = self.apiServer.GetMSByLabel(self.deploymentLabel, ms)
                    # get end points object that has deploy and ms label
                    eps = self.apiServer.GetEndPointsByLabel(self.deploymentLabel, ms)
                    pods = []
                    # loop through all pending pod
                    for pod in self.apiServer.GetPending():
                        # if ms and dep is same as the pending list's one in etcd , add it to pods list
                        # get current deployment instruction's pod
                        if pod.deploymentLabel == self.deploymentLabel:
                            if pod.microserviceLabel == ms:
                                pods.append(pod)
                    # get all rest of the port which store in etcd
                    for ep in eps:
                        pods.append(self.apiServer.GetPod(ep))
                    availableCPUS = 0
                    # once it gets all pods with associated deployment, calculate its cpu useage
                    for pod in pods:
                        availableCPUS += pod.available_cpu
                    if len(pods) == 0:
                        averageUtil = 0
                    else:
                        averageUtil = (microservice.cpuCost * len(pods) - availableCPUS) / (microservice.cpuCost * len(pods))
                    newReps = math.ceil(microservice.currentReplicas*averageUtil/self.setPoint)
                    if newReps < self.minReps:
                        microservice.expectedReplicas = self.minReps
                    elif newReps > self.maxReps:
                        microservice.expectedReplicas = self.maxReps
                    else:
                        microservice.expectedReplicas = newReps
            time.sleep(self.time)
        print("HPA Shutdown")
