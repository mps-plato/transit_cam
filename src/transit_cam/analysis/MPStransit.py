#! /usr/bin/python

# MPStransit.py
# by Rene' Heller, heller@mps.mpg.de, Max Planck Institute for Solar System Research, Goettingen, Germany
# created 2017-04-04 (MPS), last modification 2017-04-05
# -----
# Modified for Night of Science 2025 by Ilyas Kuhlemann (kuhlemann@mps.mpg.de) during June 2025.
# -----


from numpy import mean, sort, array

from transit_cam.analysis.models import LightCurve, TransitAnalysisResult


def analyze_transit(times, brightnesses):
    return (mean(times), min(brightnesses))


def lightcurve_analyze(light_curve: LightCurve) -> TransitAnalysisResult:
    times = array([point.time_diff(light_curve.first_point)
             for point in light_curve.points])
    lightcurve = array([sum(point.value) for point in light_curve.points])
    print(times.shape, lightcurve.shape)

    lightcurve_outoftrans = _get_lightcurve_out_of_transit_level(lightcurve)
    lightcurve_norm = _normalize_lightcurve(lightcurve, lightcurve_outoftrans)

    d_appr = _identify_approximate_transit_depth_by_measuring_the_three_lowest_flux_levels_and_rejecting_the_lowest_two(
        lightcurve_norm)

    # the threshold is 100 - (100 - d_appr) / 2 = (200 - (100 - d_appr)) / 2 = (200 - 100 + d_appr) / 2 = (100 + d_appr) / 2 = 50 + d_appr / 2
    threshold = 50. + d_appr / 2.

    # Identify transit centers assuming that each transit has rouhgly the same depth
    timetrans_temp = []
    lightcurvetrans_temp = []
    transit_mids = []
    transit_midfluxes = []
    transit_flag = False

    for time_j, lightcurve_norm_j in zip(times, lightcurve_norm):
        if lightcurve_norm_j < threshold:
            transit_flag = True
            timetrans_temp.append(time_j)
            lightcurvetrans_temp.append(lightcurve_norm_j)

        if lightcurve_norm_j > threshold and transit_flag:
            transit_mid_temp, transit_midflux_temp = analyze_transit(
                timetrans_temp, lightcurvetrans_temp)
            transit_mids.append(transit_mid_temp)
            transit_midfluxes.append(transit_midflux_temp)
            timetrans_temp = []
            lightcurvetrans_temp = []
            transit_flag = False
    print(transit_mids)
    period = (transit_mids[-1] - transit_mids[0]) / max((len(transit_mids)-1), 1)

    depth = 100. - mean(transit_midfluxes)

    return TransitAnalysisResult(
        period,
        float(depth),
        transit_mids,
        transit_midfluxes,
        times,
        lightcurve_norm
    )


def _identify_approximate_transit_depth_by_measuring_the_three_lowest_flux_levels_and_rejecting_the_lowest_two(lightcurve_norm):
    return sort(lightcurve_norm)[2]


def _normalize_lightcurve(lightcurve, lightcurve_outoftrans):
    return 100. / lightcurve_outoftrans * lightcurve


def _get_lightcurve_out_of_transit_level(lightcurve):
    return (mean(lightcurve[:3]) + mean(lightcurve[-3:])) / 2.
