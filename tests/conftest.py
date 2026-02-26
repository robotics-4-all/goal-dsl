import pytest

BROKER_MQTT = """
Broker<MQTT> HomeMQTT
    host: 'localhost'
    port: 1883
    auth:
        username: 'user'
        password: 'pass'
end
"""

BROKER_REDIS = """
Broker<Redis> LocalRedis
    host: 'localhost'
    port: 6379
    db: 2
    ssl: true
    auth:
        username: ''
        password: ''
end
"""

BROKER_AMQP = """
Broker<AMQP> MyAMQP
    host: 'rabbitmq.local'
    port: 5672
    vhost: '/test'
    topicExchange: 'amq.topic'
    auth:
        username: 'guest'
        password: 'guest'
end
"""

REST_ENDPOINT = """
RESTEndpoint SensorAPI
    verb: GET
    host: 'api.example.com'
    port: 443
    path: '/sensors'
end
"""

ENTITY_SENSOR = """
Entity TempSensor
    type: sensor
    topic: 'bedroom.temperature'
    source: HomeMQTT
    freq: 10
    description: 'Temperature sensor'
    attributes:
        - temp: float
        - humidity: float
        - active: bool
        - label: str
end
"""

ENTITY_ALL_TYPES = """
Entity AllTypes
    type: sensor
    topic: 'test.all'
    source: HomeMQTT
    attributes:
        - i: int
        - f: float
        - s: str
        - b: bool
        - l: list
        - d: dict
        - t: time
end
"""


@pytest.fixture
def minimal_model():
    return (
        BROKER_MQTT
        + """
Entity TempSensor
    type: sensor
    topic: 'bedroom.temp'
    source: HomeMQTT
    attributes:
        - temp: float
end

Goal<Watch> G1
    entity: TempSensor
end

Scenario S1
    goals:
        - G1
    concurrent: false
end
"""
    )


@pytest.fixture
def condition_model():
    return (
        BROKER_MQTT
        + """
Entity TempSensor
    type: sensor
    topic: 'bedroom.temp'
    source: HomeMQTT
    attributes:
        - temp: float
        - humidity: float
        - active: bool
        - label: str
end

Goal<When> NumericGoal
    when
        TempSensor.temp > 30
end

Goal<When> CompoundGoal
    when
        (TempSensor.temp > 30) AND (TempSensor.humidity < 0.5)
end

Goal<When> BoolGoal
    when
        TempSensor.active is true
end

Goal<When> AggGoal
    when
        mean(TempSensor.temp, 5) > 25
end

Scenario S1
    goals:
        - NumericGoal
        - CompoundGoal
        - BoolGoal
        - AggGoal
    concurrent: false
end
"""
    )


@pytest.fixture
def full_model():
    return """
Metadata
    name: TestProject
    version: "1.0.0"
    author: "Test Author"
    email: "test@example.com"
    description: "Test project"
end

Broker<MQTT> HomeMQTT
    host: 'localhost'
    port: 1883
    auth:
        username: ''
        password: ''
end

Broker<Redis> LocalRedis
    host: 'localhost'
    port: 6379
    auth:
        username: ''
        password: ''
end

RTMonitor
    source: LocalRedis
    eventTopic: "goaldsl.test.event"
    logsTopic: "goaldsl.test.log"
end

Entity TempSensor
    type: sensor
    topic: 'bedroom.temp'
    source: HomeMQTT
    freq: 10
    attributes:
        - temp: float
        - humidity: float
end

Entity DoorSensor
    type: sensor
    topic: 'door.state'
    source: HomeMQTT
    attributes:
        - locked: bool
end

Entity Robot1Pose
    type: sensor
    topic: 'robot.pose'
    source: HomeMQTT
    attributes:
        - position: dict
        - orientation: dict
end

Goal<Watch> G_Watch
    entity: TempSensor
end

Goal<When> G_When
    when
        (TempSensor.temp > 30) AND (TempSensor.humidity < 0.5)
    then
        - G_Watch
    config
        timeConstraints:
            - FROM_GOAL_START(<60)
        description: 'Temperature alert'
end

Goal<Eval> G_Eval
    when
        'TempSensor.temp * 2 > 50'
end

Goal<When> G_Bool
    when
        DoorSensor.locked is true
end

Goal<Cluster> G_Cluster
    goals:
        - G_Watch
        - G_When
        - G_Eval
    strategy: ALL_ACCOMPLISHED_ORDERED
end

Goal<Loop> G_Loop
    goal: G_Watch
    times: 3
end

Goal<Rect> G_Rect
    entities:
        - Robot1Pose
    bottomLeftEdge: Point3D(0, 0, 0)
    lengthX: 5
    lengthY: 5
    tag: ENTER
    timeConstraints:
        - FOR_TIME(5)
        - FROM_GOAL_START(<180)
end

Goal<Circle> G_Circle
    entities:
        - Robot1Pose
    center: Point3D(5, 5, 0)
    radius: 3
    tag: AVOID
end

Goal<Pos> G_Pos
    entity: Robot1Pose
    position: Point3D(1, 1, 0)
    maxDeviation: 0.1
end

Goal<Heading> G_Heading
    entity: Robot1Pose
    orientation: Orientation2D(1.57)
    maxDeviation: 0.05
end

Goal<Route> G_Route
    entity: Robot1Pose
    points: [Point3D(0,0,0), Point3D(1,1,0), Point3D(2,0,0)]
    maxDeviation: 0.5
end

Scenario MainScenario
    goals:
        - G_Cluster -> 0.5
        - G_Loop -> 0.3
        - G_Rect -> 0.2
    antigoals:
        - G_Bool
    concurrent: true
    tickFreq: 10
    description: 'Main test scenario'
end

Scenario SecondScenario
    goals:
        - G_Watch
        - G_When
    concurrent: false
end
"""


@pytest.fixture
def model_with_generators():
    return (
        BROKER_MQTT
        + """
Entity VirtualSensor
    type: sensor
    freq: 5
    topic: 'virtual.bme'
    source: HomeMQTT
    attributes:
        - temperature: float -> gaussian(10, 20, 5) with noise gaussian(1, 1)
        - humidity: float -> linear(1, 0.2) with noise uniform(0, 1)
        - pressure: float -> constant(0.5)
end

Goal<Watch> VG1
    entity: VirtualSensor
end

Scenario S1
    goals:
        - VG1
    concurrent: false
end
"""
    )


@pytest.fixture
def goal_status_model():
    return (
        BROKER_MQTT
        + """
Entity TempSensor
    type: sensor
    topic: 'test.temp'
    source: HomeMQTT
    attributes:
        - temp: float
end

Goal<Watch> G1
    entity: TempSensor
end

Goal<When> G2
    when
        G1.status == REACHED
end

Scenario S1
    goals:
        - G1
        - G2
    concurrent: false
end
"""
    )


@pytest.fixture
def inrange_model():
    return (
        BROKER_MQTT
        + """
Entity TempSensor
    type: sensor
    topic: 'test.temp'
    source: HomeMQTT
    attributes:
        - temp: float
end

Goal<When> G1
    when
        TempSensor.temp in range [18.0, 26.0]
end

Scenario S1
    goals:
        - G1
    concurrent: false
end
"""
    )
