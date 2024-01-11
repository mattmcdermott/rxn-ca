from __future__ import annotations

import plotly.graph_objects as go
from plotly.graph_objs.layout import YAxis,XAxis,Margin

from ..phases.solid_phase_set import SolidPhaseSet
from ..core.reaction_result import ReactionResult
from ..core.heating import HeatingSchedule
from .reaction_step_analyzer import ReactionStepAnalyzer

from ..computing.schemas.ca_result_schema import RxnCAResultDoc

from typing import Tuple, List

from pymatgen.core.composition import Composition
import numpy as np

OTHERS = "others"
class BulkReactionAnalyzer():
    """A class that stores the result of running a simulation. Keeps track of all
    the steps that the simulation proceeded through, and the set of reactions that
    was used in the simulation.
    """

    @classmethod
    def from_result_doc_file(cls, fname: str) -> BulkReactionAnalyzer:
        doc: RxnCAResultDoc = RxnCAResultDoc.from_file(fname)
        return cls(doc.results, doc.reaction_library.phases, doc.recipe.heating_schedule)

    def __init__(self, results: List[ReactionResult], phase_set: SolidPhaseSet, heating_sched: HeatingSchedule):
        """Initializes a ReactionResult with the reaction set used in the simulation

        Args:
            rxn_set (ScoredReactionSet):
        """
        self.step_analyzer = ReactionStepAnalyzer(phase_set)
        self.heating_schedule = heating_sched

        self.result_length = len(results[0])
        self.results = results

    def plot_elemental_amounts(self) -> None:
        elements = list(self.step_analyzer.get_molar_elemental_composition(self.results[0].first_step).keys())
        traces = []
        
        step_idxs, step_groups = self._get_step_groups()
        amounts = [self.step_analyzer.get_molar_elemental_composition(sg) for sg in step_groups]
        for el in elements:
            ys = [a.get(el, 0) for a in amounts]
            traces.append(go.Scatter(name=el, x=step_idxs, y=ys, mode='lines', line=dict(width=4)))

        max_x = max(set().union([t.x for t in traces]))
        fig = self._get_plotly_fig(
            "Simulation Step",
            "El. Fraction",
            "Elemental Fractions vs time step",
            max_x
        )

        for t in traces:
            fig.add_trace(t)

        fig.show()

    
    def plot_elemental_fractions(self) -> None:
        elements = list(self.step_analyzer.get_fractional_elemental_composition(self.results[0].first_step).keys())
        traces = []
        
        step_idxs, step_groups = self._get_step_groups()
        amounts = [self.step_analyzer.get_fractional_elemental_composition(sg) for sg in step_groups]
        for el in elements:
            ys = [a.get(el, 0) for a in amounts]
            traces.append(go.Scatter(name=el, x=step_idxs, y=ys, mode='lines', line=dict(width=4)))

        max_x = max(set().union([t.x for t in traces]))
        fig = self._get_plotly_fig(
            "Simulation Step",
            "El. Fraction",
            "Elemental Fractions vs time step",
            max_x
        )

        for t in traces:
            fig.add_trace(t)

        fig.show()

    def get_layout(self, x_label, y_label, title, max_x):
        return go.Layout(
            title={
                'text' : title,
                'x':0.43,
                'y': 0.92,
                'xanchor': 'center'
            },
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            width=1000, height=800,
            xaxis=XAxis(
                title=x_label,
                range=[0, max_x],
                gridcolor='black',
                mirror=True,
                ticks='outside',
                showline=True,
                linecolor='black',
            ),
            yaxis2 = YAxis(
                title=dict(
                    text="Temp (K)",
                    font=dict(
                        color='crimson'
                    )       
                ),
                gridcolor='red',
                tickfont=dict(
                    color='crimson'
                ),
                overlaying= 'y', 
                side= 'right',
                ticks='outside',
                showline=True,  
                linecolor='black',      
            ),
            yaxis=dict(
                title=dict(
                    text=y_label,
                ),
                gridcolor='black',
                range=(0, None),
                side='left',
                ticks='outside',
                showline=True,    
                linecolor='black',    
            ),
            legend=dict(
                x=1.2,
                y=0.6,
                borderwidth=2
            ),
            font=dict(
                family="Lato",
                size=18,
            )            
        )

    def _get_plotly_fig(self, x_label, y_label, title, max_x):
        layout = self.get_layout(x_label, y_label, title, max_x)

        fig = go.Figure(layout=layout)        

        fig.add_trace(self.get_heating_trace())
        
        return fig
    
    def get_heating_trace(self):
        heating_xs, heating_ys = self.heating_schedule.get_xy_for_plot()
        return go.Scatter(
            name="Temperature",
            x=heating_xs,
            y=heating_ys,
            mode='lines',
            yaxis='y2',
            line = dict(color='crimson', width=4, dash='dash')
        )
    
    def get_mole_fraction_traces(self, min_prevalence=0.01, phases=None):
        """In a Jupyter Notebook environment, plots the phase prevalence traces for the simulation.

        Returns:
            None:
        """

        step_idxs, step_groups = self._get_step_groups()

        traces = []
        mole_fraction_breakdowns = [self.step_analyzer.get_all_mole_fractions(sg) for sg in step_groups]

        if phases is None:
            phases = set()
            for bd in mole_fraction_breakdowns:
                phases = phases.union(set(bd.keys()))
        
        for phase in phases:
            ys = [mb.get(phase, 0) for mb in mole_fraction_breakdowns]
            traces.append((step_idxs, ys, phase))

        filtered_traces = [t for t in traces if max(t[1]) > min_prevalence]

        go_traces = [go.Scatter(name=t[2], x=t[0], y=t[1], mode='lines', line=dict(width=4)) for t in filtered_traces]
        return go_traces
    
    def molar_fractional_breakdown(self, step_no, include_melted: bool = True):
        return self.step_analyzer.get_all_absolute_molar_amounts(self.get_steps(step_no), include_melted=include_melted)

    def get_all_absolute_molar_amounts(self, step_no: int, include_melted: bool = True):
        return self.step_analyzer.get_all_absolute_molar_amounts(self.get_steps(step_no), include_melted=include_melted)

    def plot_mole_fractions(self, min_prevalence=0.01) -> None:
        """In a Jupyter Notebook environment, plots the phase prevalence traces for the simulation.

        Returns:
            None:
        """

        traces = self.get_mole_fraction_traces(min_prevalence)
        max_x = max(set().union([t.x for t in traces]))

        fig = self._get_plotly_fig(
            "Simulation Step",
            "Prevalence",
            "Prevalence by Simulation Step",
            max_x
        )

        for t in traces:
            fig.add_trace(t)

        return fig
    
    def get_steps(self, step_no):
        return [r.get_step(step_no) for r in self.results]
    
    def get_final_steps(self):
        return [r.last_step for r in self.results]

    def get_first_steps(self):
        return [r.first_step for r in self.results]

    def get_molar_phase_traces(self, min_prevalence=0.01, xrd_adjust=True, phases=None, legend="legend1") -> None:
        """In a Jupyter Notebook environment, plots the phase prevalence traces for the simulation.

        Returns:
            None:
        """
        step_idxs, step_groups = self._get_step_groups()
        
        traces = []
        molar_breakdowns = [self.step_analyzer.get_all_absolute_molar_amounts(step_group) for step_group in step_groups]

        if phases is None:
            phases = set()
            for bd in molar_breakdowns:
                phases = phases.union(set(bd.keys()))
            
        for phase in phases:
            if phase is not SolidPhaseSet.FREE_SPACE:
                ys = np.array([mb.get(phase, 0) for mb in molar_breakdowns])
            
                if xrd_adjust:
                    comp = Composition(phase)
                    ys = ys * comp.num_atoms

                traces.append((step_idxs, ys, phase))

        filtered_traces = [t for t in traces if max(t[1]) > min_prevalence]

        go_traces = [go.Scatter(name=t[2], x=t[0], y=t[1], mode='lines', line=dict(width=4), legend=legend) for t in filtered_traces]
        return go_traces
    

    def plot_molar_phase_amounts(self, min_prevalence=0.01, xrd_adjust=False, phases=None) -> None:
        """In a Jupyter Notebook environment, plots the phase prevalence traces for the simulation.

        Returns:
            None:
        """
        traces = self.get_molar_phase_traces(min_prevalence, xrd_adjust=xrd_adjust, phases=phases)

        if xrd_adjust:
            ylabel = "# of Moles (weighted by # atoms)"
        else:
            ylabel = "# of Moles"

        fig = self._get_plotly_fig(
            "Simulation Step",
            ylabel,
            "Absolute Molar Prevalence by Simulation Step",
            None
        )

        for t in traces:
            fig.add_trace(t)

        return fig
    
    def get_mole_trace(self, phase_name, xrd_adjust=False):
        step_idxs, step_groups = self._get_step_groups()
        molar_breakdowns = [self.step_analyzer.get_all_absolute_molar_amounts(step_group) for step_group in step_groups]

        ys = np.array([mb.get(phase_name, 0) for mb in molar_breakdowns])
            
        if xrd_adjust:
            comp = Composition(phase_name)
            ys = ys * comp.num_atoms

        return ys
    
    def plot_groups(self, group_defs):
        step_idxs, step_groups = self._get_step_groups()

        traces = []
        molar_breakdowns = [self.step_analyzer.get_all_mole_fractions(sg) for sg in step_groups]


        phases = set()
        for bd in molar_breakdowns:
            phases = phases.union(set(bd.keys()))

        traces = {}

        for group_name, group_members in group_defs.items():
            group_trace = np.array([0 for _ in molar_breakdowns])

            for phase in phases:
                if phase in group_members and phase is not SolidPhaseSet.FREE_SPACE:
                    ys = [mb.get(phase, 0) for mb in molar_breakdowns]
                    group_trace = group_trace + ys
            
            traces[group_name] = group_trace

        go_traces = []

        for trace_name, trace_data in traces.items():
            tr = go.Scatter(
                name=trace_name, 
                x=step_idxs,
                y=trace_data,
                mode='lines',
                line=dict(width=4),
                stackgroup='one'
            )

            go_traces.append(tr)

        fig = self._get_plotly_fig(
            "Simulation Step",
            "# of Moles",
            "Absolute Molar Prevalence by Simulation Step",
            None
        )

        fig.add_traces(go_traces)

        fig.show()
        
        

    def plot_phase_volumes(self):
        """In a Jupyter Notebook environment, plots the phase prevalence traces for the simulation.

        Returns:
            None:
        """

        step_idxs, step_groups = self._get_step_groups()

        fig = self._get_plotly_fig(
            "Simulation Step",
            "Volume",
            "Phase Volume by Simulation Step",
            step_idxs[-1]
        )
        
        traces = []
        vol_breakdowns = [self.step_analyzer.get_all_absolute_phase_volumes(step_group) for step_group in step_groups]

        phases = set()
        for bd in vol_breakdowns:
            phases = phases.union(set(bd.keys()))
            
        for phase in phases:
            if phase != SolidPhaseSet.FREE_SPACE:
                ys = [mb.get(phase, 0) for mb in vol_breakdowns]
                traces.append((step_idxs, ys, phase))

        filtered_traces = [t for t in traces if max(t[1]) > 0.1]

        for t in filtered_traces:
            fig.add_trace(go.Scatter(name=t[2], x=t[0], y=t[1], mode='lines'))

        fig.show()        

    def as_dict(self):
        return {
            "@module": self.__class__.__module__,
            "@class": self.__class__.__name__,
            "steps": [s.as_dict() for s in self.steps],
            "rxn_set": self.rxn_set.as_dict(),
            "phase_set": self.phase_set.as_dict()
        }

    def _get_step_groups(self) -> Tuple[List[int], List]:
        num_points = min(100, self.result_length)
        step_size = max(1, round(self.result_length / num_points))
        [r.load_steps(step_size) for r in self.results]
        step_idxs = list(range(0, self.result_length, step_size))
        return step_idxs, [[r.get_step(step_idx) for r in self.results] for step_idx in step_idxs]