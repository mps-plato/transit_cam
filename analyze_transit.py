import os.path as path
import MPStransit
import numpy
from pylab import *
from matplotlib.backends.backend_pdf import PdfPages


class LightPoint(object):
    def __init__(self, timestamp, value):
        self.timestamp = timestamp
        self.value = value

    @staticmethod
    def parse_line(line):
        parts = line.strip().split()
        if len(parts) != 5:
            return None
        timestamp = datetime.datetime.strptime(' '.join(parts[0:2])[:26], '%Y-%m-%d %H:%M:%S.%f')
        value = array((float(parts[2][1:-1]), float(parts[3][:-1]), float(parts[4][:-1])))
        return LightPoint(timestamp, value)
        
    def time_diff(self, other):
        if isinstance(other, datetime.datetime):
            return float((self.timestamp - other).total_seconds()) 
        return float((self.timestamp - other.timestamp).total_seconds())
        

class LightCurve(object):
    def __init__(self, points):
        self.points = points
        self.update_duration()
        self.first_point = None
        self.last_point = None
        
    def update_duration(self):
        self.first_point = sorted(self.points, key=lambda v: v.timestamp)[0]
        self.last_point = sorted(self.points, key=lambda v: v.timestamp)[-1]
        
    def get_duration(self):
        return self.last_point.time_diff(self.first_point)
        
    @staticmethod
    def read(filename):
        result = []
        with open(filename) as in_file:
            current_curve = []
            for i, line in enumerate(in_file.readlines()):
                if line[0] == '#':
                    if len(current_curve) > 0:
                        result.append(LightCurve(current_curve))
                        print(f'Creating light curve with {len(current_curve)} elements and '
                              f'a duration of {result[-1].get_duration()}')
                    current_curve = []
                    continue
                new_point = LightPoint.parse_line(line)
                if new_point is None: 
                    print('Unexpected number of parts on line {}'.format(i))
                    continue
                current_curve.append(new_point)                
            if len(current_curve) > 0:
                result.append(LightCurve(current_curve))
                print(f'Creating light curve with {len(current_curve)} elements and '
                      f'a duration of {result[-1].get_duration()}')
        print(f'{len(result)} light curves read')
        return result
        
    def extract(self, from_time, to_time):
        return LightCurve([point for point in self.points if from_time <= point.timestamp < to_time])
        
    def split(self, separators):
        result = []
        new_curve = []
        index = 0
        for point in sorted(self.points, key=lambda v: v.timestamp):
            if point.timestamp < separators[index]:
                new_curve.append(point)
            else:
                if len(new_curve):
                    result.append(LightCurve(new_curve))
                    new_curve = []
                index += 1
                if index >= len(separators):
                    break
        if len(new_curve):
            result.append(LightCurve(new_curve))
        return result
        
    def get_norm(self):
        return numpy.mean([mean(point.value) for point in self.points[:3]+self.points[-3:]])
        
    def get_min(self):
        return sorted([mean(point.value) for point in self.points])[2]
        
    def normalize(self):
        return LightCurve([LightPoint(point.timestamp, 100.*point.value/self.get_norm()) for point in self.points])
        
    def get_transit_center(self):
        threshold = (self.get_norm() + self.get_min()) / 2.
        # mean_time = mean([point.time_diff(self.first_point)
        #                   for point in self.points if mean(point.value) <= threshold])
#         return self.first_point.timestamp+datetime.timedelta(seconds=mean_time)
        
        mean_time_obscuration = mean([point.time_diff(self.first_point)*(self.get_norm()-mean(point.value))
                                      for point in self.points if mean(point.value) <= threshold])
        mean_obscuration = self.get_norm()-mean([mean(point.value) for point in self.points if mean(point.value) <=
                                                 threshold])
        return self.first_point.timestamp+datetime.timedelta(seconds=mean_time_obscuration/mean_obscuration)
        
    def invert(self, timestamp):
        return LightCurve([LightPoint(timestamp-(point.timestamp-timestamp), point.value) for point in self.points])    
    

def add_plot_info(an_axis, period, num_curves, depth):
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

    
def analyze_file(filename):
    if not path.isfile(filename):
        print('File {} not found. Aborting'.format(filename))
        return
        
    light_curves = LightCurve.read(filename)
    for light_curve in reversed(light_curves):
        times = [point.time_diff(light_curve.first_point) for point in light_curve.points]
        values = [sum(point.value) for point in light_curve.points]
        period, depth, transit_centers = MPStransit.lightcurve_analyze(array(times), array(values), True)
        clipped_curves = []
        for transit_center in transit_centers:
            clipped_curve = light_curve.extract(light_curve.first_point.timestamp +
                                                datetime.timedelta(seconds=transit_center - period / 2.),
                                                light_curve.first_point.timestamp +
                                                datetime.timedelta(seconds=transit_center + period / 2.))
            clipped_curves.append(clipped_curve.normalize())

        print(len(clipped_curves))

        fig = figure(1, dpi=400)
        fig.set_size_inches((8.27, 11.69))
        fig.clf()
        fig.suptitle('Nacht des Wissens 2022 - MPS')
#         plt1 = subplot(111)
        plt1 = subplot(211)
        for clipped_curve in clipped_curves[0::2]:
            transit_center = clipped_curve.get_transit_center()
            curve_time = [point.time_diff(transit_center) for point in clipped_curve.points]
            light_curve_points = [mean(point.value) for point in clipped_curve.points]
            plot(curve_time, light_curve_points)
        for clipped_curve in clipped_curves[1::2]:
            transit_center = clipped_curve.get_transit_center()
            curve_time = [point.time_diff(transit_center) for point in clipped_curve.invert(transit_center).points]
            light_curve_points = [mean(point.value) for point in clipped_curve.points]
            plot(curve_time, light_curve_points)
        plt1.set_title('Gespiegelte Lichtkurve')
        add_plot_info(gca(), period, len(light_curves), depth)
        
        plt1 = subplot(212)
        for clipped_curve in clipped_curves:
            transit_center = clipped_curve.get_transit_center()
            curve_time = [point.time_diff(transit_center) for point in clipped_curve.points]
            light_curve_points = [mean(point.value) for point in clipped_curve.points]
            plot(curve_time, light_curve_points)
        plt1.set_title('Direkte Lichtkurve')
        current_axis = gca()
        add_plot_info(current_axis, period, len(light_curves), depth)
        
        # add timestamp at the bottom right
        figtext(0.99, 0.01, light_curve.first_point.timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
                size="xx-small", horizontalalignment="right")

        try:
            filename = light_curve.first_point.timestamp.strftime('Nacht des Wissens 2022 - %Y_%m_%d_%H_%M_%S.pdf')
            pdf = PdfPages(filename)
            savefig(pdf, format="pdf")
            pdf.close()
        except PermissionError:
            print('File {} is in use'.format(filename))
        subplots_adjust(hspace=0.4)
        show()
        draw()


def main():
    for filename in sys.argv[1:]+[r'transit_cam.log']: 
        analyze_file(filename)


if __name__ == '__main__':
    main()
