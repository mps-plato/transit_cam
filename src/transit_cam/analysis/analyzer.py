
from dataclasses import dataclass
from pathlib import Path
import datetime
from math import sqrt
from numpy import array, mean

from transit_cam.analysis.models import LightCurve

from transit_cam.analysis import MPStransit


@dataclass
class AnalyzeFileArgs:
    input_file: Path
    create_pdf: bool
    number_of_lightcurves: int
    planet_name: str


class Analyzer:

    def __init__(self) -> None:
        pass

    def analyze_file(self, args: AnalyzeFileArgs) -> None:
        print(f'Analyzing {args.number_of_lightcurves} light curves from file {args.input_file} with name {args.planet_name} and {"" if args.create_pdf else "not "}writing to PDF')
        if not args.input_file.exists():
            print(f'File {args.input_file} not found. Aborting')
            return

        light_curves = list(reversed(LightCurve.read(args.input_file)))
        if args.number_of_lightcurves > 0:
            light_curves = light_curves[:args.number_of_lightcurves]
        for light_curve in light_curves:
            self._analyze_lightcurve(light_curve, len(light_curves))

    def _analyze_lightcurve(
        self, 
        light_curve: LightCurve, 
        number_of_lightcurves: int
    ):
        times = [point.time_diff(light_curve.first_point)
                 for point in light_curve.points]
        values = [sum(point.value) for point in light_curve.points]
        period, depth, transit_centers = MPStransit.lightcurve_analyze(
            array(times), array(values), True)
        clipped_curves = []
        for transit_center in transit_centers:
            clipped_curve = light_curve.extract(light_curve.first_point.timestamp +
                                                datetime.timedelta(
                                                    seconds=transit_center - period / 2.),
                                                light_curve.first_point.timestamp +
                                                datetime.timedelta(seconds=transit_center + period / 2.))
            clipped_curves.append(clipped_curve.normalize())

        print(len(clipped_curves))

        fig = figure(1, dpi=400)
        fig.set_size_inches((8.27, 11.69))
        fig.clf()
        fig.suptitle(f'Nacht des Wissens 2022 - {planet_name}')
    #         plt1 = subplot(111)
        plt1 = subplot(211)
        for clipped_curve in clipped_curves[0::2]:
            transit_center = clipped_curve.get_transit_center()
            curve_time = [point.time_diff(transit_center)
                          for point in clipped_curve.points]
            light_curve_points = [mean(point.value)
                                  for point in clipped_curve.points]
            plot(curve_time, light_curve_points)
        for clipped_curve in clipped_curves[1::2]:
            transit_center = clipped_curve.get_transit_center()
            curve_time = [point.time_diff(
                transit_center) for point in clipped_curve.invert(transit_center).points]
            light_curve_points = [mean(point.value)
                                  for point in clipped_curve.points]
            plot(curve_time, light_curve_points)
        plt1.set_title('Gespiegelte Lichtkurve')
        add_plot_info(gca(), period, number_of_lightcurves, depth)

        plt1 = subplot(212)
        for clipped_curve in clipped_curves:
            transit_center = clipped_curve.get_transit_center()
            curve_time = [point.time_diff(transit_center)
                          for point in clipped_curve.points]
            light_curve_points = [mean(point.value)
                                  for point in clipped_curve.points]
            plot(curve_time, light_curve_points)
        plt1.set_title('Direkte Lichtkurve')
        current_axis = gca()
        add_plot_info(current_axis, period, number_of_lightcurves, depth)

        # add timestamp at the bottom right
        figtext(0.99, 0.01, light_curve.first_point.timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
                size="xx-small", horizontalalignment="right")

        if no_pdf is False:
            try:
                filename = light_curve.first_point.timestamp.strftime(
                    'Nacht des Wissens 2022 - %Y_%m_%d_%H_%M_%S.pdf')
                pdf = PdfPages(filename)
                savefig(pdf, format="pdf")
                pdf.close()
            except PermissionError:
                print('File {} is in use'.format(filename))
        subplots_adjust(hspace=0.4)
        show()
        draw()


    def _add_plot_info(
        self, an_axis, period, num_curves, depth
    ):
        an_axis.set_ylabel(MPStransit.YAXIS)
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
