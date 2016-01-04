""" Contains the Accelerometer """

import time
import math
from mpf.system.device import Device


class Accelerometer(Device):
    """Implements an accelerometer

    Args: Same as the Device parent class

    """

    config_section = 'accelerometers'
    collection = 'accelerometers'
    class_label = 'accelerometer'

    def __init__(self, machine, name, config, collection=None, validate=True):
        super(Accelerometer, self).__init__(machine, name, config, collection,
                                     platform_section='accelerometers',
                                     validate=validate)

        self.platform.configure_accelerometer(self,
            number=self.config['number'],
            useHighPass=False)
        self.history = False
        self.value = False

    def received_hit(self):
        # currently unused
        self.log.debug("Received hit above threshold %s",
                config['hit_limits'].keys()[0])
        self.machine.events.post(config['hit_limits'].values()[0])

    def _calculate_vector_length(self, x, y, z):
        return math.sqrt(x*x + y*y + z*z)

    def _calculate_angle(self, x1, y1, z1, x2, y2, z2):
        return math.acos((x1*x2 + y1*y2 + z1*z2) /
                (self._calculate_vector_length(x1, y1, z1) *
                self._calculate_vector_length(x2, y2, z2)))

    def update_acceleration(self, x, y, z):
        self.value = (x, y, z)

        if not self.history:
            self.history = (x, y, z)
            dx = dy = dz = 0
        else:
            dx = x - self.history[0]
            dy = y - self.history[1]
            dz = z - self.history[2]

            alpha = 0.95
            self.history = (self.history[0] * alpha + x * (1-alpha),
                            self.history[1] * alpha + y * (1-alpha),
                            self.history[2] * alpha + z * (1-alpha))

        self._handle_hits(dx, dy, dz)
        self._handle_level(x, y, z)

    def _handle_level(self, x, y ,z):
        deviation_total = self._calculate_angle(self.config['level_x'],
                                self.config['level_y'], self.config['level_z'],
                                x, y, z)
        deviation_x = self._calculate_angle(0, self.config['level_y'],
                                self.config['level_z'], 0, y, z)
        deviation_y = self._calculate_angle(self.config['level_x'], 0,
                                self.config['level_z'], x, 0, z)
        for max_deviation in self.config['level_limits']:
            if deviation_total/math.pi*180 > max_deviation:
                self.log.debug("Deviation x: %s, y: %s, total: %s",
                    deviation_x/math.pi*180,
                    deviation_y/math.pi*180,
                    deviation_total/math.pi*180)
                self.machine.events.post(self.config['level_limits'][max_deviation],
                    deviation_total=deviation_total,
                    deviation_x=deviation_x,
                    deviation_y=deviation_y)

            

    def _handle_hits(self, dx, dy ,dz):
        acceleration = self._calculate_vector_length(dx, dy, dz)
        for min_acceleration in self.config['hit_limits']:
            if acceleration > min_acceleration:
                self.log.debug("Received hit of %s > %s. Posting %s",
                    acceleration,
                    min_acceleration,
                    self.config['hit_limits'][min_acceleration]
                )
                self.machine.events.post(self.config['hit_limits'][min_acceleration])
