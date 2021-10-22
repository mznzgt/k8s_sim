from api_server import APIServer
import threading
import time

# monitor workerNode object and update endpoint
class NodeController:
    def __init__(self, APISERVER, LOOPTIME):
        self.apiServer = APISERVER
        self.running = True
        self.time = LOOPTIME

    def __call__(self):
        print("NodeController start")
        while self.running:
            pods = []
            crashedPods = []
            with self.apiServer.etcdLock:
                # loop through all pod
                for pod in self.apiServer.etcd.runningPodList:
                    # if pod is running, add it to pods list
                    # if pod is terminating but requests are not all done, add to pods list as well
                    if pod.status == "RUNNING":
                        pods.append(pod)
                    elif pod.status == "TERMINATING":
                        if not(all(p.done() for p in pod.requests)):
                            pods.append(pod)
                        else:
                            # if pod is terminating and all requests are handled, shut down the pool
                            pod.pool.shutdown()
                    else:
                        # if pod is failed
                        crashedPods.append(pod)
                    # update running pods
                    self.apiServer.etcd.runningPodList = pods
                    # loop through crash pods
                    for pod in crashedPods:
                        for endPoint in self.apiServer.etcd.endPointList:
                            # if any crashedpods is in endPointList in etcd
                            if endPoint.pod == pod:
                                # make that pod to pending
                                pod.status = "PENDING"
                                pod.crash.clear()
                                # add it to pendingPodList in etcd
                                self.apiServer.etcd.pendingPodList.append(pod)
                                # remove this endpoint as it's not up to date
                                self.apiServer.RemoveEndPoint(endPoint)
                                break
            time.sleep(self.time)
        print("NodeContShutdown")