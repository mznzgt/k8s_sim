import threading

class Microservice:
    def __init__(self, INFOLIST):
        self.microserviceLabel = INFOLIST [0]
        self.deploymentLabel = ''
        self.currentReplicas = 0
        self.expectedReplicas = 1
        self.handlingTime = int(INFOLIST[2])
        self.cpuCost = int(INFOLIST[1])
