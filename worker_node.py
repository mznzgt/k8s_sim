class WorkerNode:
    def __init__(self,INFOLIST):
        self.label = INFOLIST[0]
        self.assigned_cpu = int(INFOLIST[1])
        self.available_cpu = int(INFOLIST[1])
        self.status = 'UP'