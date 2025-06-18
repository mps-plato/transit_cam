
from dataclasses import dataclass
from pathlib import Path
import datetime
from math import sqrt, isnan
import logging

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

    _logger = logging.getLogger("transit_cam.Analyzer")

    def __init__(self) -> None:
        pass

    def analyze_file(self, args: AnalyzeFileArgs) -> None:
        self._logger.info(
            f'Analyzing {args.number_of_lightcurves} light curves from file {args.input_file} with name {args.planet_name} and {"" if args.create_pdf else "not "}writing to PDF')
        if not args.input_file.exists():
            self._logger.warning(f'File {args.input_file} not found. Aborting')
            return

        light_curves: list[LightCurve] = list(
            reversed(LightCurve.read(args.input_file)))
        if args.number_of_lightcurves > 0:
            light_curves = light_curves[:args.number_of_lightcurves]
        for light_curve in light_curves:
            self._plot_single_light_curve(args, light_curve)

    def _plot_single_light_curve(
        self,
        args: AnalyzeFileArgs,
        light_curve: LightCurve
    ) -> None:
        analysis_result: transit_cam.analysis.models.TransitAnalysisResult = MPStransit.lightcurve_analyze(
            light_curve
        )
        filename = light_curve.first_point.timestamp.strftime(
            'Nacht des Wissens 2025 - %Y_%m_%d_%H_%M_%S.pdf')
        self._logger.info("Writing pdf to %s", filename)

        with matplotlib.backends.backend_pdf.PdfPages(filename) as pdf:
            fig1: matplotlib.figure.Figure = self._create_figure_with_full_lightcurve_plot(
                analysis_result
            )
            pdf.savefig(fig1)
            plt.close()
            if not isnan(analysis_result.period) and analysis_result.period > 0:
                fig2: matplotlib.figure.Figure = self._create_figure_with_folded_lightcurve_plot(
                    light_curve,
                    analysis_result,
                    args.planet_name
                )
                pdf.savefig(fig2)
                plt.close()
            else:
                self._logger.info(
                    "lightcurve_analyze has not found a period => skipping folded light curve plots")

        # plt.show()

    def _create_figure_with_full_lightcurve_plot(
        self,
        analysis_result: transit_cam.analysis.models.TransitAnalysisResult
    ) -> matplotlib.figure.Figure:
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

        for label in legend.get_texts():
            label.set_fontsize('small')

        return fig

    def _create_figure_with_folded_lightcurve_plot(
        self,
        light_curve: LightCurve,
        transit_characteristica: transit_cam.analysis.models.TransitAnalysisResult,
        planet_name: str
    ) -> matplotlib.figure.Figure:
        period, depth, transit_centers = (
            transit_characteristica.period,
            transit_characteristica.depth,
            transit_characteristica.transit_mids
        )
        clipped_curves = []
        for transit_center in transit_centers:
            self._logger.debug("transit_center = %f; period = %f", transit_center, period)
            t_start = (light_curve.first_point.timestamp +
                       datetime.timedelta(seconds=transit_center - period / 2.))
            t_end = (light_curve.first_point.timestamp +
                     datetime.timedelta(seconds=transit_center + period / 2.))
            self._logger.debug("Extracting timespan from %s to %s", t_start, t_end)
            clipped_curve = light_curve.extract(t_start, t_end)
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
        self._add_plot_info(ax1, period, len(clipped_curves), depth)

        ax2: matplotlib.axes.Axes = fig.add_subplot(212)
        for clipped_curve in clipped_curves:
            transit_center = clipped_curve.get_transit_center()
            curve_time = [point.time_diff(transit_center)
                          for point in clipped_curve.points]
            light_curve_points = [mean(point.value)
                                  for point in clipped_curve.points]
            ax2.plot(curve_time, light_curve_points)
        ax1.set_title('Direkte Lichtkurve')
        self._add_plot_info(ax2, period, len(clipped_curves), depth)

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
