
class OneAheadSensor:

    def __init__(self, world):
        self.world = world
        self.leader = None

    def orient(self, car):
        """
        find the car that is directly ahead of car
        :param car:
        :return:
        """
        leader = None
        cars = sorted(self.world.cars, key=lambda car: -car.pos)
        for c in cars:
            if car.name == c.name:
                self.leader = leader
                break
            else:
                leader = c


    def sense(self):
        if self.leader is not None:
            return self.leader.pos, self.leader.vel
        else:
            return None, None

    def __str__(self):
        if self.leader is not None:
            return "ONE_AHEAD(%s.pos, %s.vel)" % (self.leader.name, self.leader.name)
        else:
            return "NONE_AHEAD"
