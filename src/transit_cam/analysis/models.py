from dataclasses import dataclass
import datetime

from pylab import array, mean
import numpy.typing as npt
import numpy as np


class LightPoint:
    def __init__(self, timestamp: datetime.datetime, value: npt.NDArray[np.float64]):
        self.timestamp = timestamp
        self.value = value

    @staticmethod
    def parse_line(line):
        parts = line.strip().split()
        if len(parts) != 5:
            return None
        timestamp = datetime.datetime.strptime(
            ' '.join(parts[0:2])[:26], '%Y-%m-%d %H:%M:%S.%f')
        value = array(
            (float(parts[2][1:-1]), float(parts[3][:-1]), float(parts[4][:-1])))
        return LightPoint(timestamp, value)

    def time_diff(self, other):
        if isinstance(other, datetime.datetime):
            return float((self.timestamp - other).total_seconds())
        return float((self.timestamp - other.timestamp).total_seconds())


class LightCurve:
    def __init__(
        self, points: list[LightPoint]
    ):
        self.points = points
        self.first_point: LightPoint
        self.last_point: LightPoint
        self.update_duration()

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

    def extract(
        self,
        from_time: datetime.datetime,
        to_time: datetime.datetime
    ) -> 'LightCurve':
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
        return mean([mean(point.value) for point in self.points[:3]+self.points[-3:]])

    def get_min(self):
        return sorted([mean(point.value) for point in self.points])[2]

    def normalize(self):
        return LightCurve([LightPoint(point.timestamp, 100.*point.value/self.get_norm()) for point in self.points])

    def get_transit_center(self):
        threshold = (self.get_norm() + self.get_min()) / 2.

        mean_time_obscuration = mean([point.time_diff(self.first_point)*(self.get_norm()-mean(point.value))
                                      for point in self.points if mean(point.value) <= threshold])
        mean_obscuration = self.get_norm()-mean([mean(point.value) for point in self.points if mean(point.value) <=
                                                 threshold])
        return self.first_point.timestamp+datetime.timedelta(seconds=mean_time_obscuration/mean_obscuration)

    def invert(self, timestamp):
        return LightCurve([LightPoint(timestamp-(point.timestamp-timestamp), point.value) for point in self.points])


@dataclass
class TransitAnalysisResult:
    period: float
    depth: float
    transit_mids: list[float]
    transit_mid_fluxes: list[float]
    timestamps: npt.NDArray[np.float64]
    percent_normalized_flux: npt.NDArray[np.float64]
