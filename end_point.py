class EndPoint:
    def __init__(self, POD, DEPLABEL, MSLABEL, NODE,):
        self.pod = POD
        self.microserviceLabel = MSLABEL
        self.deploymentLabel = DEPLABEL
        self.node =NODE