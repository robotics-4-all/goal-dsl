#!/usr/bin/env python3

from goalee import Target, RedisMiddleware
from goalee.topic_goals import TopicMessageReceivedGoal, TopicMessageParamGoal


if __name__ == '__main__':
    middleware = RedisMiddleware()
    t = Target(middleware)

    g = TopicMessageReceivedGoal(topic='robot.opts.face_detection.detected')

    t.add_goal(g)
    g = TopicMessageParamGoal(topic='robot.sensor.qr.detected',
                              condition=lambda msg: True if msg["msg"] == "R4A" else False)
    t.add_goal(g)
    g = TopicMessageParamGoal(topic='robot.sensor.sonar.front',
                              condition=lambda msg: True if msg["range"] < 10.0 else False)
    t.add_goal(g)
    g = TopicMessageParamGoal(topic='robot.sensor.motion.base',
                              condition=lambda msg: True if (msg["angVel"] < 0.5 and msg["linVel"] > 3.0) else False)
    t.add_goal(g)
    g = TopicMessageParamGoal(topic='robot.sensor.motion.base',
                              condition=lambda msg: True if ((msg["linVel"] > 10 and msg["angVel"] < 0.5) and msg["error"] == "") else False)
    t.add_goal(g)
    g = TopicMessageParamGoal(topic='robot.sensor.face.detected',
                              condition=lambda msg: True if "error" in msg["msg"] else False)
    t.add_goal(g)
    g = TopicMessageParamGoal(topic='robot.sensor.face.detected',
                              condition=lambda msg: True if "error" not in msg["msg"] else False)
    t.add_goal(g)

    t.run_seq()
