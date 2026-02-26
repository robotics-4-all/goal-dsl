class BrokerAuthPlain:
    def __init__(self, parent=None, username=None, password=None, **kwargs):
        self.parent = parent
        self.username = username
        self.password = password


class Broker:
    def __init__(
        self, parent=None, name=None, host=None, port=None, auth=None, ssl=None, **kwargs
    ):
        self.parent = parent
        self.name = name
        self.host = host
        self.port = port
        self.auth = auth
        self.ssl = ssl if ssl is not None else False


class MQTTBroker(Broker):
    def __init__(
        self,
        parent=None,
        name=None,
        host=None,
        port=None,
        auth=None,
        ssl=False,
        basePath="",
        webPath="/mqtt",
        webPort=8883,
        **kwargs,
    ):
        super().__init__(parent, name, host, port, auth, ssl)
        self.basePath = basePath
        self.webPath = webPath
        self.webPort = webPort


class AMQPBroker(Broker):
    def __init__(
        self,
        parent=None,
        name=None,
        host=None,
        port=None,
        vhost=None,
        auth=None,
        topicE="amq.topic",
        rpcE="DEFAULT",
        ssl=False,
        **kwargs,
    ):
        super().__init__(parent, name, host, port, auth, ssl)
        self.vhost = vhost
        self.topicExchange = topicE
        self.rpcExchange = rpcE


class RedisBroker(Broker):
    def __init__(
        self, parent=None, name=None, host=None, port=None, auth=None, db=0, ssl=False, **kwargs
    ):
        super().__init__(parent, name, host, port, auth, ssl)
        self.db = db
