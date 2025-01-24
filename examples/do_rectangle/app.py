#!/usr/bin/env python

import sys
import time
from typing import Dict

from commlib.msg import PubSubMessage, MessageHeader
from pydantic import Field
from commlib.node import Node


"""_summary_
This example demonstrates how to create a simple robot that moves to a specific position.
The robot's position is published to the `robot_1.pose` topic.
"""


class PoseMessage(PubSubMessage):
    # header: MessageHeader = MessageHeader()
    position: Dict[str, float] = Field(
        default_factory=lambda: {'x': 0.0, 'y': 0.0, 'z': 0.0})
    orientation: Dict[str, float] = Field(
        default_factory=lambda: {'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0})


class Robot(Node):
    def __init__(self, name, connection_params, pose_uri, velocity=2,
                 *args, **kwargs):
        self.name = name
        self.pose = PoseMessage()
        self.pose_uri = pose_uri
        self.velocity = velocity
        super().__init__(node_name=name, connection_params=connection_params,
                         *args, **kwargs)
        self.pose_pub = self.create_publisher(msg_type=PoseMessage,
                                              topic=self.pose_uri)

    def move(self, x, y, interval=0.5):
        vel = self.velocity
        current_x = self.pose.position['x']
        current_y = self.pose.position['y']

        distance = ((x - current_x)**2 + (y - current_y)**2)**0.5
        distance_x = x - current_x
        distance_y = y - current_y
        steps_x = abs(distance_x) / vel
        steps_y = abs(distance_y) / vel
        direction_x = 1 if distance_x > 0 else -1
        direction_y = 1 if distance_y > 0 else -1

        for _ in range(int(steps_x / interval)):
            current_x += vel * direction_x * interval
            # current_x += vel * direction_x * interval
            distance = ((x - current_x)**2 + (y - current_y)**2)**0.5
            self.publish_pose(current_x, current_y)
            print(f'Current position: x={current_x:.2f}, y={current_y:.2f}')
            print(f'Distance to target: {distance:.2f}')
            time.sleep(interval)
        for _ in range(int(steps_y / interval)):
            current_y += vel * direction_y * interval
            distance = ((x - current_x)**2 + (y - current_y)**2)**0.5
            self.publish_pose(current_x, current_y)
            print(f'Current position: x={current_x:.2f}, y={current_y:.2f}')
            print(f'Distance to target: {distance:.2f}')
            time.sleep(interval)

    def publish_pose(self, x, y):
        self.pose.position['x'] = x
        self.pose.position['y'] = y
        self.pose_pub.publish(self.pose)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        from commlib.transports.redis import ConnectionParameters
    elif sys.argv[1] == "redis":
        from commlib.transports.redis import ConnectionParameters
    elif sys.argv[1] == "mqtt":
        from commlib.transports.mqtt import ConnectionParameters
    elif sys.argv[1] == "amqp":
        from commlib.transports.amqp import ConnectionParameters

    conn_params = ConnectionParameters(reconnect_attempts=0)

    robot_1 = Robot(name='robot_1', connection_params=conn_params,
                    pose_uri='gn_robot_1.pose.internal', heartbeats=False)

    try:
        robot_1.run()
        robot_1.move(5, 0)
        robot_1.move(5, 5)
        robot_1.move(0, 5)
        robot_1.move(0, 0)
        robot_1.stop()
    except KeyboardInterrupt:
        robot_1.stop()
