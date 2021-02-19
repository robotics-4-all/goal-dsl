#!/usr/bin/env python3

from goalee import Target, RedisMiddleware
from goalee.topic_goals import TopicMessageReceivedGoal, TopicMessageParamGoal


if __name__ == '__main__':
    middleware = RedisMiddleware()
    t = Target(middleware, name='MyAppTarget',
               score_weights=[0.3333333333333333, 0.3333333333333333, 0.3333333333333333])

    g = RectangleAreaGoal(topic='',
                          name='GoalA',
                          bottom_left_edge=Point(2.0, 6.0),
                          length_x=3.0,
                          length_y=4.0,
                          max_duration=None,
                          min_duration=None)
    t.add_goal(g)
    g = CircularAreaGoal(topic='',
                         name='GoalB',
                         center=Point(2.0, 6.0),
                         radius=3.0,
                         max_duration=None,
                         min_duration=None)
    t.add_goal(g)
    t.add_goal(g)

    t.run_concurrent()
