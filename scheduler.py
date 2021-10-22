from api_server import APIServer
import threading
import time

class Scheduler(threading.Thread):
    def __init__(self, APISERVER, LOOPTIME):
        self.apiServer = APISERVER
        self.running = True
        self.time = LOOPTIME

    def __call__(self):
        print("Scheduler start")
        while self.running:
            newPending = []
            # get all worker nodes from etcd
            workers = self.apiServer.etcd.nodeList
            with self.apiServer.etcdLock:
                # loop through all pending pod
                for pod in self.apiServer.etcd.pendingPodList:
                    workers.sort(key=lambda x:x.available_cpu, reversed=True)
                    # if a worker node status is up and node's resource > pod(microservice) resource
                    # pod will be running and - the pod resource and create endpoint
                    # also add pod to runningPodList
                    for worker in workers:
                        if worker.status == "UP":
                            if worker.available_cpu >= pod.assigned_cpu:
                                pod.status = "RUNNING"
                                worker.available_cpu -= pod.assigned_cpu
                                self.apiServer.CreateEndPoint(pod, worker)
                                self.apiServer.etcd.runningPodList.append(pod)
                                break
                    # add pending pod to etcd's pendingPod list
                    if pod.status == "PENDING":
                        newPending.append(pod)
                self.apiServer.etcd.pendingPodList = newPending
            time.sleep(self.time)
        print("SchedShutdown")

