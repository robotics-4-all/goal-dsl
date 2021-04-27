#!/usr/bin/env python3

from goalee import Target, RedisMiddleware
from goalee.topic_goals import TopicMessageReceivedGoal, TopicMessageParamGoal
from goalee.area_goals import RectangleAreaGoal, CircularAreaGoal
from goalee.complex_goal import ComplexGoal, ComplexGoalAlgorithm
from goalee.types import Point


if __name__ == '__main__':
    middleware = RedisMiddleware()
    t = Target(middleware, name='MyAppTarget',
               score_weights=[0.3333333333333333, 0.3333333333333333, 0.3333333333333333])

    g = ComplexGoal(name='GoalC',
                    max_duration=None,
                    min_duration=None)
    gs = RectangleAreaGoal(topic='',
                           name='GoalA',
                           bottom_left_edge=Point(2.0, 6.0),
                           length_x=3.0,
                           length_y=4.0,
                           max_duration=10.0,
                           min_duration=0.0)
    g.add_goal(gs)
    gs = CircularAreaGoal(topic='',
                          name='GoalB',
                          center=Point(2.0, 6.0),
                          radius=3.0,
                          max_duration=10.0,
                          min_duration=0.0)
    g.add_goal(gs)
    ## More Goals to Generate here
    t.add_goal(g)
    g = ComplexGoal(name='GoalD',
                    max_duration=None,
                    min_duration=None)
    gs = RectangleAreaGoal(topic='',
                           name='GoalA',
                           bottom_left_edge=Point(2.0, 6.0),
                           length_x=3.0,
                           length_y=4.0,
                           max_duration=10.0,
                           min_duration=0.0)
    g.add_goal(gs)
    gs = CircularAreaGoal(topic='',
                          name='GoalB',
                          center=Point(2.0, 6.0),
                          radius=3.0,
                          max_duration=10.0,
                          min_duration=0.0)
    g.add_goal(gs)
    ## More Goals to Generate here
    t.add_goal(g)
    g = ComplexGoal(name='GoalE',
                    max_duration=None,
                    min_duration=None)
    gs = RectangleAreaGoal(topic='',
                           name='GoalA',
                           bottom_left_edge=Point(2.0, 6.0),
                           length_x=3.0,
                           length_y=4.0,
                           max_duration=10.0,
                           min_duration=0.0)
    g.add_goal(gs)
    gs = CircularAreaGoal(topic='',
                          name='GoalB',
                          center=Point(2.0, 6.0),
                          radius=3.0,
                          max_duration=10.0,
                          min_duration=0.0)
    g.add_goal(gs)
    ## More Goals to Generate here
    t.add_goal(g)

    t.run_seq()
