from api_server import APIServer
import threading
import time

#control and terminates pod object based on the expected number of replicaas
class DepController:
    def __init__(self, APISERVER, LOOPTIME):
        self.apiServer = APIServer
        self.running = True
        self.time = LOOPTIME

    def __call__(self):
        print("depController start")
        while self.running:
            microservices = []
            with self.apiServer.etcdLock:
                # loop through all microservice from etcd
                for microservice in self.apiServer.etcd.microserviceList:
                    # if currentRep < expectedRep, increase pod by 1
                    while microservice.currentReplicas < microservice.expectedReplicas:
                        self.apiServer.CreatePod(microservice)
                        microservice.currentReplicas +=1
                    endPoints = self.apiServer.GetEndPointsByLabel(microservice.deploymentLabel, microservice.microserviceLabel)
                    # Remove any pending pods before terminating running ones
                    # get all pending pod from etcd
                    for pod in self.apiServer.etcd.pendingPodList:
                        # if microservice is pending
                        if pod.microserviceLabel == microservice.microserviceLabel:
                            if pod.microserviceLabel == microservice.deploymentLabel:
                                # and if current > expect
                                if microservice.currentReplicas > microservice.expectedReplicas:
                                    # remove this pending pod and -1 for replicas
                                    self.apiServer.etcd.pendingPodList.remove(pod)
                                    microservice.currentReplicas -=1
                    # this loop's microservice endpoint object
                    for endPoint in endPoints:
                        #Terminate running pods if required
                        # if current > expected, terminate pod and replicas -1
                        if microservice.currentReplicas > microservice.expectedReplicas:
                            self.apiServer.TerminatePod(endPoint)
                            microservice.currentReplicas -=1
                    # refresh the microservice list
                    microservices.append(microservice)
                self.apiServer.etcd.microserviceList = microservices
            time.sleep(self.time)
        print("DepContShutdown")
