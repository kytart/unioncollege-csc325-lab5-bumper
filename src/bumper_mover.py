#!/usr/bin/env python
import rospy, math, random
from geometry_msgs.msg import Twist
from kobuki_msgs.msg import BumperEvent

BUMPER_LEFT = 0
BUMPER_CENTER = 1
BUMPER_RIGHT = 2

BUMPER_STATE_RELEASED = 0
BUMPER_STATE_PRESSED = 1

pub = rospy.Publisher('/cmd_vel_mux/input/teleop', Twist, queue_size=10)

class Turtlebot:

    def __init__(self):
        self.linear_speed = 0.2
        self.angular_speed = degrees2radians(30.0)
        self.evasion_angle = degrees2radians(90)
        self.bump = None

    def start(self):
        while not rospy.is_shutdown():
            self.move()
            self.backUp(1.0)
            self.bump = None

    def bumped(self, bumper):
        self.bump = bumper

    def move(self, distance = None, isForward = True, interrupt_on_bump = True):
        outData = Twist()
        t0 = rospy.get_rostime().secs
        current_distance = 0
        rate = rospy.Rate(10)

        while not rospy.is_shutdown() and t0 == 0:
            t0 = rospy.get_rostime().secs

        outData.linear.x = self.linear_speed if isForward else -self.linear_speed

        while (
            not rospy.is_shutdown() and
            (distance is None or current_distance < distance)
        ):
            if interrupt_on_bump and not self.bump is None:
                rospy.loginfo('bump detected: %d', self.bump)
                break

            pub.publish(outData)

            t1 = rospy.get_rostime().secs
            current_distance = self.linear_speed * (t1 - t0)

            rate.sleep()

        outData.linear.x = 0.0
        pub.publish(outData)
        rate.sleep()

    def rotate(self, relative_angle, isClockwise):
        outData = Twist()

        t0 = rospy.get_rostime().secs
        current_angle = 0
        rate = rospy.Rate(10)

        while not rospy.is_shutdown() and t0 == 0:
            t0 = rospy.get_rostime().secs

        outData.angular.z = -self.angular_speed if isClockwise else self.angular_speed

        while not rospy.is_shutdown() and current_angle < relative_angle:
            pub.publish(outData)

            t1 = rospy.get_rostime().secs
            current_angle = self.angular_speed * (t1 - t0)

            rate.sleep()

        outData.angular.z = 0.0
        pub.publish(outData)
        rate.sleep()

    def backUp(self, distance):
        self.move(distance, False, False)

        if self.bump == BUMPER_LEFT:
            rospy.loginfo('rotate right')
            self.rotate(self.evasion_angle, True)
        elif self.bump == BUMPER_RIGHT:
            rospy.loginfo('rotate left')
            self.rotate(self.evasion_angle, False)
        else:
            rospy.loginfo('rotate random')
            self.rotate(self.evasion_angle, random.choice([True, False]))


def degrees2radians(angle):
    return angle * (math.pi / 180.0)


def handle_bump(event, robot):
    if event.state == BUMPER_STATE_PRESSED:
        robot.bumped(event.bumper)


def init():
    robot = Turtlebot()

    rospy.init_node('turtle_bumper_mover', anonymous=True)

    rospy.Subscriber(
        '/mobile_base/events/bumper',
        BumperEvent,
        handle_bump,
        robot
    )

    robot.start()


if __name__ == '__main__':
    init()
