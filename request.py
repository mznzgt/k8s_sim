import threading

class Request:
    def __init__(self, INFOLIST):
        self.label = INFOLIST[0]
        self.deploymentLabel = INFOLIST[1]
        self.fail = threading.Event()