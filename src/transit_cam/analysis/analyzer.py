
from dataclasses import dataclass
from pathlib import Path
import datetime
from math import sqrt
import matplotlib.axes
import matplotlib.backends.backend_pdf
import matplotlib.figure
from numpy import mean

import matplotlib.pyplot as plt
import matplotlib

from transit_cam.analysis.models import LightCurve
from transit_cam.analysis import MPStransit
import transit_cam.analysis.models


@dataclass
class AnalyzeFileArgs:
    input_file: Path
    create_pdf: bool
    number_of_lightcurves: int
    planet_name: str


YAXIS = 'Relative Helligkeit (%)'


class Analyzer:

    def __init__(self) -> None:
        pass

    def analyze_file(self, args: AnalyzeFileArgs) -> None:
        print(f'Analyzing {args.number_of_lightcurves} light curves from file {args.input_file} with name {args.planet_name} and {"" if args.create_pdf else "not "}writing to PDF')
        if not args.input_file.exists():
            print(f'File {args.input_file} not found. Aborting')
            return

        light_curves: list[LightCurve] = list(
            reversed(LightCurve.read(args.input_file)))
        if args.number_of_lightcurves > 0:
            light_curves = light_curves[:args.number_of_lightcurves]
        for light_curve in light_curves:
            analysis_result: transit_cam.analysis.models.TransitAnalysisResult = MPStransit.lightcurve_analyze(
                light_curve
            )
            fig1: matplotlib.figure.Figure = self._create_figure_with_full_lightcurve_plot(
                analysis_result
            )
            fig2: matplotlib.figure.Figure = self._create_figure_with_lightcurve_plot(
                light_curve,
                analysis_result,
                len(light_curves),
                args.planet_name
            )
            if args.create_pdf:
                filename = light_curve.first_point.timestamp.strftime(
                    'Nacht des Wissens 2025 - %Y_%m_%d_%H_%M_%S.pdf')
                print("Writing pdf to", filename)
                with matplotlib.backends.backend_pdf.PdfPages(filename) as pdf:                    
                    pdf.savefig(fig1)                    
                    pdf.savefig(fig2)
            # plt.show()

    def _create_figure_with_full_lightcurve_plot(
        self,
        analysis_result: transit_cam.analysis.models.TransitAnalysisResult
    ) -> matplotlib.figure.Figure:
        period, depth = (
            analysis_result.period,
            analysis_result.depth
        )

        print("Transit Period =  {:3f} s".format(period))
        print("Transit Depth  = {:1f} %".format(depth))

        print("\n==> The planet has a radius that is {:3f} times the radius of the star.".format(
            sqrt(depth/100.)))

        fig = plt.figure(1)
        ax1 = fig.add_subplot(111)
        ax1.plot(
            analysis_result.timestamps,
            analysis_result.percent_normalized_flux,
            color="black", label='Messungen'
        )
        ax1.plot(
            analysis_result.transit_mids,
            analysis_result.transit_mid_fluxes,
            '*', color="red", label='Tiefpunkte'
        )

        ax1.set_ylabel(YAXIS)
        ax1.set_xlabel("Zeit (s)")

        legend = ax1.legend(loc='upper right')
        # Set the fontsize
        for label in legend.get_texts():
            label.set_fontsize('small')

        return fig

    def _create_figure_with_lightcurve_plot(
        self,
        light_curve: LightCurve,
        transit_characteristica: transit_cam.analysis.models.TransitAnalysisResult,
        number_of_lightcurves: int,
        planet_name: str
    ) -> matplotlib.figure.Figure:
        period, depth, transit_centers = (
            transit_characteristica.period,
            transit_characteristica.depth,
            transit_characteristica.transit_mids
        )
        clipped_curves = []
        for transit_center in transit_centers:
            print(light_curve.first_point.timestamp)
            print(transit_center)
            print(period)
            clipped_curve = light_curve.extract(light_curve.first_point.timestamp +
                                                datetime.timedelta(
                                                    seconds=transit_center - period / 2.),
                                                light_curve.first_point.timestamp +
                                                datetime.timedelta(seconds=transit_center + period / 2.))
            clipped_curves.append(clipped_curve.normalize())

        fig = plt.figure(1, dpi=400)
        fig.set_size_inches((8.27, 11.69))
        fig.clear()
        fig.suptitle(f'Nacht des Wissens 2025 - {planet_name}')
        ax1: matplotlib.axes.Axes = fig.add_subplot(211)
        for clipped_curve in clipped_curves[0::2]:
            transit_center = clipped_curve.get_transit_center()
            curve_time = [point.time_diff(transit_center)
                          for point in clipped_curve.points]
            light_curve_points = [mean(point.value)
                                  for point in clipped_curve.points]
            ax1.plot(curve_time, light_curve_points)
        for clipped_curve in clipped_curves[1::2]:
            transit_center = clipped_curve.get_transit_center()
            curve_time = [point.time_diff(
                transit_center) for point in clipped_curve.invert(transit_center).points]
            light_curve_points = [mean(point.value)
                                  for point in clipped_curve.points]
            ax1.plot(curve_time, light_curve_points)
        ax1.set_title('Gespiegelte Lichtkurve')
        self._add_plot_info(ax1, period, number_of_lightcurves, depth)

        ax2: matplotlib.axes.Axes = fig.add_subplot(212)
        for clipped_curve in clipped_curves:
            transit_center = clipped_curve.get_transit_center()
            curve_time = [point.time_diff(transit_center)
                          for point in clipped_curve.points]
            light_curve_points = [mean(point.value)
                                  for point in clipped_curve.points]
            ax2.plot(curve_time, light_curve_points)
        ax1.set_title('Direkte Lichtkurve')
        self._add_plot_info(ax2, period, number_of_lightcurves, depth)

        # add timestamp at the bottom right
        fig.text(0.99, 0.01, light_curve.first_point.timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
                 size="xx-small", horizontalalignment="right")
        fig.tight_layout()
        return fig

    def _add_plot_info(
        self, an_axis, period, num_curves, depth
    ):
        an_axis.set_ylabel(YAXIS)
        an_axis.set_xlabel('Zeit nach Tiefpunkt (s)')
        an_axis.text(0.99, 0.16, "n = {} Durchgaenge".format(num_curves), size="xx-small",
                     transform=an_axis.transAxes, horizontalalignment="right", verticalalignment="bottom")
        an_axis.text(0.99, 0.11, "T = {:5.2f} Sekunde".
                     format(period),
                     size="xx-small", horizontalalignment="right", transform=an_axis.transAxes, verticalalignment="bottom")
        an_axis.text(0.99, 0.06, "d = {:5.2f}%".format(depth, sqrt(depth / 100.)),
                     size="xx-small", horizontalalignment="right", transform=an_axis.transAxes, verticalalignment="bottom")
        an_axis.text(0.99, 0.01, "r/R = {:5.3f}".format(sqrt(depth / 100.)),
                     size="xx-small", horizontalalignment="right", transform=an_axis.transAxes, verticalalignment="bottom")
