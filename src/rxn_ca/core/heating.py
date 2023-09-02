from typing import List

from monty.json import MSONable
import numpy as np
import matplotlib.pyplot as plt

class HeatingStep(MSONable):
    """Captures the information about a single step during a heating schedule.
    """

    @classmethod
    def hold(cls, temperature, duration):
        return cls(duration, temperature)
    
    @classmethod
    def sweep(cls, t0, tf, stage_length = 2000, step_size = 100):
        if t0 == tf:
            raise ValueError("Initial and final temperatures cannot be the same!")
    
        if tf < t0:
            step_size = -step_size

        temps = list(np.arange(t0,tf,step_size))
        temps.append(tf)
        return [cls(stage_length, t) for t in temps]
        

    def __init__(self, duration, temp):
        self.duration = duration
        self.temp = temp

    def as_dict(self):
        return (self.duration, self.temp)

class HeatingSchedule(MSONable):
    """Captures the information of a heating schedule, e.g. ramping up
    to a particular temperature, holding, and then cooling back down
    """

    def __init__(self, *args):
        # schedules at first can just be a series of steps, e.g.:
        # 2000 steps, 300k
        # 5000 steps, 900k
        # 2000 steps 500k
        self.steps: List[HeatingStep] = []

        for step in args:
            if type(step) is list:
                for s in step:
                    self.steps.append(s)
            else:
                self.steps.append(step)
    
    @property
    def all_temps(self):
        return list(set([s.temp for s in self.steps]))

    def as_dict(self):
        return [step.as_dict() for step in self.steps]
    
    def plot(self):
        fig, axs = plt.subplots()
        total_length = sum([s.duration for s in self.steps])

        curr_x = 0
        xs = []
        ys = []

        for step in self.steps:
            xs.append(curr_x)
            ys.append(step.temp)
            curr_x += step.duration

        axs.plot(xs, ys)
        axs.hlines(298, -100, total_length + 100, color='r')
        axs.set_title("Heating Schedule")
        axs.set_ylabel("Temperature (K)")
        axs.set_xlabel("Rxn. Coordinate")