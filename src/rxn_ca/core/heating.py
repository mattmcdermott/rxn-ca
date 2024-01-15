from typing import List

from monty.json import MSONable
import numpy as np
import matplotlib.pyplot as plt

class HeatingStep(MSONable):
    """Captures the information about a single step during a heating schedule.
    """

    @classmethod
    def hold(cls, temperature, duration, stage_length = 1):
        return [cls(stage_length, temperature) for _ in range(duration)]
    
    @classmethod
    def sweep(cls, t0, tf, stage_length = 1, temp_step_size = 100):
        if t0 == tf:
            raise ValueError("Initial and final temperatures cannot be the same!")
    
        if tf < t0:
            temp_step_size = -temp_step_size

        temps = [int(s) for s in np.arange(t0,tf,temp_step_size)]
        temps.append(tf)
        return [cls(stage_length, t) for t in temps]

    @classmethod
    def from_dict(cls, d):
        return cls(
            d["duration"],
            d["temperature"]
        )

    def __init__(self, duration, temp):
        self.duration = duration
        self.temp = temp

    def as_dict(self):
        return {
            "duration": self.duration, 
            "temperature": self.temp
        }

class HeatingSchedule(MSONable):
    """Captures the information of a heating schedule, e.g. ramping up
    to a particular temperature, holding, and then cooling back down
    """
    
    @classmethod
    def from_dict(cls, d):
        steps = [HeatingStep.from_dict(s) for s in d['steps']]
        sched = cls(steps)
        return sched

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
        d = super().as_dict()
        return {**d, **{
            "steps": [step.as_dict() for step in self.steps]
        }}
    
    def temp_at(self, step_idx):
        tallied = 0
        for step in self.steps:
            tallied += step.duration
            if tallied > step_idx:
                return step.temp
            
    def get_xy_for_plot(self, step_size: int):
        curr_x = 0
        xs = []
        ys = []


        for step in self.steps:
            xs.append(curr_x)
            ys.append(step.temp)
            curr_x += step.duration * step_size
            xs.append(curr_x)
            ys.append(step.temp)            

        if len(self.steps) == 1:
            xs.append(self.steps[0].duration * step_size)
            ys.append(self.steps[0].temp)

        return xs, ys        
    
    def plot(self):
        fig, axs = plt.subplots()
        total_length = sum([s.duration for s in self.steps])

        xs, ys = self.get_xy_for_plot()

        axs.plot(xs, ys)
        axs.hlines(298, -100, total_length + 100, color='r')
        axs.set_title("Heating Schedule")
        axs.set_ylabel("Temperature (K)")
        axs.set_xlabel("Rxn. Coordinate")
    
    def __len__(self):
        return len(self.steps)