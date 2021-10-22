from deployment import Deployment
from microservice import Microservice
from end_point import EndPoint
from etcd import Etcd
from Pod import Pod
from request import Request
from worker_node import WorkerNode
import threading
import random
import copy
import re

class APIServer:
    def __init__(self):
        self.etcd = Etcd()
        self.etcdLock = threading.Lock()
        self.requestWaiting = threading.Event()

    def CreateWorker(self, info):
        worker = WorkerNode(info)
        self.etcd.nodeList.append(worker)
        # print("Worker_Node " + worker.label + " created")

    # because deployment asscioated with microservice's template
    def CreateDepolyment(self, info):
        deployment = Deployment(info)
        # add deployment to etcd's deployment list
        self.etcd.deploymentList.append(deployment)
        # exact mspath to mslist
        mslist = re.split("\+|\.|\(|\)", deployment.msPath)
        # remove '' in mslist
        while '' in mslist: mslist.remove('')
        # the exact mslist is now the proper deployment.mslist
        deployment.msList = mslist
        # for each ms in dep.mslist from the dep instruction
        for ms in deployment.msList:
            # for each ms template in etcd microTempList
            for msTemplate in self.etcd.microserviceTemplates:
                # if this ms is stored in etcd's msTemp list
                if msTemplate.microserviceLabel == ms:
                    # append this microservice to microserviceList
                    # as it's called from dep instriction which it has
                    # been found from microvice template that is stored
                    # in etcd's msTemplateList
                    depMS = copy.copy(msTemplate)
                    depMS.deploymentLabel = deployment.deploymentLabel
                    self.etcd.microserviceList.append(depMS)
        # print("Deployment " + deployment.deploymentLabel + " created")

    # add microservice template to etcd microTempList
    def CreateMicroserviceTemplate(self,info):
        microservice = Microservice(info)
        self.etcd.microserviceTemplates.append(microservice)

    # add endpoint to etcd's endPointList
    def CreateEndPoint(self, pod, worker):
        endPoint = EndPoint(pod, pod.deploymentLabel, pod.microserviceLabel, worker)
        self.etcd.endPointList.append(endPoint)
        # print("New Endpoint for "+endPoint.deploymentLabel+"- NODE: "+ endPoint.node.label + " POD: " + endPoint.pod.podName)

    # get all deployments from etcd deploymentList
    def GetDeployments(self):
        return self.etcd.deploymentList.copy()

    # get all node(worker) from etcd's nodeList
    def GetWorkers(self):
        return self.etcd.nodeList.copy()

    # get the whole pendingPodList from etcd
    def GetPending(self):
        return self.etcd.pendingPodList.copy()

    # get all endPointList from etcd
    def GetEndPoints(self):
        return self.etcd.endPointList.copy()

    # return a list of EndPoints associated with a given deployment and microservice
    def GetEndPointsByLabel(self,  deploymentLabel, microserviceLabel):
        endPoints = []
        for endPoint in self.etcd.endPointList:
            if endPoint.deploymentLabel == deploymentLabel:
                if endPoint.microserviceLabel == microserviceLabel:
                    endPoints.append(endPoint)
        return endPoints

    # return a deployment object given a deploymentLabel
    def GetDepByLabel(self, deploymentLabel):
        deployments = list(filter(lambda x: x.deploymentLabel == deploymentLabel, self.etcd.deploymentList))
        if len(deployments == 1):
            return deployments[0]
        else:
            print('Deployment ' + deploymentLabel + ' not found')

    # return a microservice object given a mslabel and a delabel
    def GetMSByLabel(self, msLabel, depLabel):
        microserives = list(lambda x: x.microviceLabel == msLabel, filter (lambda x:x.deploymentLabel == depLabel, self.etcd.microserviceList))
        if(len(microserives) == 1):
            return microserives[0]
        else:
            print('MS ' + msLabel + ' DEP ' + depLabel + ' not found')

    # remove a given endPoint and return CPU useage from pod back to node
    def RemoveEndPoint(self, endPoint):
        endPoint.node.available_cpu += endPoint.pod.assigned_cpu
        # print("Removing EndPoint for: "+endPoint.deploymentLabel)
        self.etcd.endPointList(endPoint)

    # remove given deployment
    def RemoveDeployment(self, info):
        dep = self.GetDepByLabel(info[0])
        dep.waiting.set()

    # make target microservice's expected pod to be 0
    def Removemicroservice(self, info):
        for ms in self.etcd.microserviceList:
            if ms.microserviceLabel == info[0]:
                ms.expectedReplicas = 0

    # generate random pod name and make sure they are not be the same name as other pods
    def GeneratePodName(self):
        label = random.randint(111,999)
        for pod in self.etcd.runningPodList:
            if pod.podName == label:
                label = self.GeneratePodName()
        for pod in self.etcd.pendingPodList:
            if pod.podName == label:
                label = self.GeneratePodName()
        return label

    # generate a podName and create a pod = microservice
    def CreatePod(self, microservice):
        podName = microservice.microserviceLabel + "_" + str(self.GeneratePodName())
        pod = Pod(podName, microservice.cpuCost, microservice.deploymentLabel, microservice.microserviceLabel, microservice.handlingTime)
        # print("Pod " + pod.podName + " created")
        self.etcd.pendingPodList.append(pod)

    # get pod given a endpoit object
    def GetPod(self,endPoint):
        if endPoint.pod == None:
            print("No Pod Found")
        else:
            return endPoint.pod

    # remove endpoint and stop a pod
    def TerminatePod(self, endPoint):
        pod = endPoint.pod
        pod.status = "TERMINATING"
        self.RemoveEndPoint(endPoint)
        # print("Terminating "+pod.podName)

    # find a pod from a given deployment therefore pod's utilitsation will be 0
    def CrashPod(self, info):
        dep = self.GetDepByLabel(info[0])
        ms = random.choice(dep.msList)
        endPoints = self.GetEndPointsByLabel(info[0],ms)
        if len (endPoints) ==0:
            print("No Pods to crash")
        else:
            pod = self.GetPod(endPoints[0])
            pod.status = "FAILED"
            pod.crash.set()
            # print ("Pod "+pod.podName+" crashed")

    # Push request to deployment instad of etcd
    def PushReq(self, info):
        self.etcd.reqCreator.submit(self.ReqPusher,info)

    # place the request to deployment's pendingReqsList
    def ReqPusher(self, info):
        deployment = self.GetDepByLabel(info[1])
        with deployment.lock:
            deployment.pendingReqs.append(Request(info))
            deployment.waiting.set()




