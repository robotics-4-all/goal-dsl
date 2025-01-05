#!/usr/bin/env python

import sys
import time
from typing import Dict

from commlib.msg import PubSubMessage, MessageHeader
from pydantic import Field
from commlib.node import Node
from commlib.transports.mqtt import ConnectionParameters


"""_summary_
This example demonstrates how to create a simple robot that moves to a specific position.
The robot's position is published to the `robot_1.pose` topic.
"""


class PoseMessage(PubSubMessage):
    # header: MessageHeader = MessageHeader()
    position: Dict[str, float] = Field(
        default_factory=lambda: {'x': 0.0, 'y': 0.0, 'z': 0.0})
    orientation: Dict[str, float] = Field(
        default_factory=lambda: {'x': 0.0, 'y': 0.0, 'z': 0.0})


class Robot(Node):
    def __init__(self, name, connection_params, pose_uri, velocity=0.5,
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
        steps_x = distance_x / vel
        steps_y = distance_y / vel
        direction_x = 1 if steps_x > 0 else -1
        direction_y = 1 if steps_y > 0 else -1

        for _ in range(int(steps_x / interval)):
            current_x += vel * direction_x * interval
            distance = ((x - current_x)**2 + (y - current_y)**2)**0.5
            self.publish_pose(current_x, current_y)
            print(f'Current position: {current_x}, {current_y}')
            print(f'Distance to target: {distance}')
            time.sleep(interval)
        for _ in range(int(steps_y / interval)):
            current_y += vel * direction_y * interval
            distance = ((x - current_x)**2 + (y - current_y)**2)**0.5
            self.publish_pose(current_x, current_y)
            print(f'Current position: {current_x}, {current_y}')
            print(f'Distance to target: {distance}')
            time.sleep(interval)

    def publish_pose(self, x, y):
        self.pose.position['x'] = x
        self.pose.position['y'] = y
        self.pose_pub.publish(self.pose)


if __name__ == '__main__':
    conn_params = ConnectionParameters(reconnect_attempts=0)

    robot_1 = Robot(name='robot_1', connection_params=conn_params,
                    pose_uri='robot_1.pose', heartbeats=False)

    try:
        robot_1.run()
        robot_1.move(3, 3)
        robot_1.stop()
    except KeyboardInterrupt:
        robot_1.stop()
