
from enum import Enum

from cacc import util
from .util import *

class ControlMode(Enum):
    CACC_CA = 1
    CACC_GC = 2
    ACC = 3


class Car:

    def __init__(self, name, init_pos, init_vel, init_accel, max_vel, max_deccel, length, guide_strat, comm_strat, sensor):
        self.name = name
        self.points = [(init_pos, init_vel, init_accel, ControlMode.CACC_GC)]
        self.max_vel = max_vel
        self.max_deccel = max_deccel
        self.length = length
        self.guide_strat = guide_strat
        self.comm_strat = comm_strat
        self.sensor = sensor

    def __str__(self):
        pos, vel, acc, mode = self.points[-1]
        return "%s p=%.2f, v=%.2f, a=%.2f, mode=%s, length=%.2f, max_deccel=%.2f, %s, %s, %s" % \
            (self.name, pos, vel, acc, mode, self.length, self.max_deccel, self.guide_strat, self.comm_strat, self.sensor)

    def __repr__(self):
        return str(self)

    def update(self, world):
        accel = self.accel
        vel = self.vel + self.accel * world.dt
        pos = self.pos + self.vel * world.dt + .5 * self.accel * world.dt ** 2
        mode = self.mode
        self.points.append((pos, vel, accel, mode))

    def update_guidance(self):
        pos, vel, _, _ = self.points[-1]
        new_acc, new_mode = self.guide_strat.compute_guidance(self)
        self.points[-1] = (pos, vel, new_acc, new_mode)

    def prepare(self):
        self.sensor.orient(self)
        self.guide_strat.orient(self)

    def communicate(self):
        self.comm_strat.communicate(self)

    @property
    def pos(self):
        return self.points[-1][0]

    @property
    def vel(self):
        return self.points[-1][1]

    @property
    def accel(self):
        return self.points[-1][2]

    @property
    def mode(self):
        return self.points[-1][3]


class World:

    def __init__(self, safe_time_gap, dt):
        self.cars = []
        self.time = 0.0
        self.safe_time_gap = safe_time_gap
        self.dt = dt
        self.messages = dict()

    def update(self):
        self.time += self.dt

        for car in self.cars:
            car.update(self)

        for car in self.cars:
            car.communicate()

        for car in self.cars:
            car.update_guidance()

    def prepare(self):
        for car in self.cars:
            car.prepare()

        for car in self.cars:
            car.communicate()

        for car in self.cars:
            car.update_guidance()

    def send_msg(self, src, data):
        self.messages[src] = data

    def recv_msg(self, src):
        return self.messages.get(src, None)

    def add_car(self, car):
        self.cars.append(car)

    def __str__(self):
        string = ""
        for car in self.cars:
            string += "t=%.2f: %s\n" % (self.time, car)
        return string


class Simulator:

    def __init__(self, conf):
        self.config = conf
        self.world = World(self.config.sim_conf['safe_time_gap'],
                           self.config.sim_conf['time_unit'])
        for car in conf.cars:
            self.world.add_car(
                Car(car['name'],
                    car['pos'],
                    car['vel'],
                    car['accel'],
                    conf.sim_conf['max_vel'],
                    conf.sim_conf['max_deccel'],
                    conf.sim_conf['car_length'],
                    util.cls_from_str(car['guide_strat'])(self.world),
                    util.cls_from_str(car['comm_strat'])(self.world),
                    util.cls_from_str(car['sensor'])(self.world)
                ))

    def run(self):
        point_count = self.config.sim_conf['trajectory_points']
        try:
            print(self.world)
            self.world.prepare()
            for _ in range(point_count):
                print(self.world)
                self.world.update()
            print(self.world)
        except (CollisionException, NegativeSafegapException, CollisionAvoidanceException) as e:
            print(e)
            exit(1)
