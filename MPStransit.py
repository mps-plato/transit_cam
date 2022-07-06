#! /usr/bin/python

# MPStransit.py
# by Rene' Heller, heller@mps.mpg.de, Max Planck Institute for Solar System Research, Goettingen, Germany
# created 2017-04-04 (MPS), last modification 2017-04-05

#import numpy
from pylab import *
import re

#seterr(all='warn')  # one message is prompted in the terminal, for an error occuring repeatedly there is no new message
seterr(all='ignore') # nothing is prompted
#seterr(all='raise') # Stops the program and points at the error
#seterr(all='print') # seems to be the default mode; prints an error message in the terminal but doesn't stop the program

def analyze_transit(times, brightnesses):
    return (mean(times), min(brightnesses))

YAXIS = 'Relative Helligkeit (%)'

#### 1. DEFINE FUNCTION FOR PABLO ####

def lightcurve_analyze(time, lightcurve, show_plot=False):  # where time and lightcurve must be arrays of the same dimension and length
    
    # Define out-of-transit level
    lightcurve_outoftrans = ( mean( lightcurve[:3] ) + mean( lightcurve[-3:] )) / 2.
    
    # Normalize light curve to 100 percent
    lightcurve_norm = 100. / lightcurve_outoftrans * lightcurve
    
    # Identify the approximate transit depth by measuring the three lowest flux levels and rejecting the two lowest of them
    d_appr = sort(lightcurve_norm)[2]
    # the threshold is 100 - (100 - d_appr) / 2 = (200 - (100 - d_appr)) / 2 = (200 - 100 + d_appr) / 2 = (100 + d_appr) / 2 = 50 + d_appr / 2
    threshold = 50. + d_appr / 2.
    
    # Identify transit centers assuming that each transit has rouhgly the same depth
    timetrans_temp = []
    lightcurvetrans_temp = []
    transit_mids = []
    transit_midfluxes = []
    transit_flag = False
    
    for time_j, lightcurve_norm_j in zip(time, lightcurve_norm):
        if lightcurve_norm_j < threshold:
            transit_flag = True
            timetrans_temp.append(time_j)
            lightcurvetrans_temp.append(lightcurve_norm_j)
        
        if lightcurve_norm_j > threshold and transit_flag:
            transit_mid_temp, transit_midflux_temp = analyze_transit(timetrans_temp, lightcurvetrans_temp)
            transit_mids.append(transit_mid_temp)
            transit_midfluxes.append(transit_midflux_temp)
            timetrans_temp = []
            lightcurvetrans_temp = []
            transit_flag = False

    period = (transit_mids[-1] - transit_mids[0]) / (len(transit_mids)-1)

    depth = 100. - mean(transit_midfluxes)
    
    if show_plot:
        print("Transit Period =  {:3f} s".format(period))
        print("Transit Depth  = {:1f} %".format(depth))
        
        print("\n==> The planet has a radius that is {:3f} times the radius of the star.".format(sqrt(depth/100.)))
        
        figure(1)
        clf()
        plt1 = subplot(111)
        plot(time, lightcurve_norm, color="black", label='Messungen')
        plot(transit_mids, transit_midfluxes, '*', color="red", label='Tiefpunkte')

        plt1.set_ylabel(YAXIS)
        plt1.set_xlabel("Zeit (s)")
        
        legend = plt1.legend(loc='upper right')
        # Set the fontsize
        for label in legend.get_texts():
            label.set_fontsize('small')

        show()
        draw()
        
    return period, depth, transit_mids


#### 2. LOAD EXAMPLE DATA ####

def get_sec(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)

# the code for the main program shall be written inside a function called main
# this is not mandatory but makes it much easier to use
def main():
    file_in = open("transit_cam.log", "r")
#     file_in = open("transit_cam_002.log", "r")
    lines_in = [line for line in file_in.readlines() if line[0] != '#']
    
    # use list comprehension
    pattern = re.compile('[ \(\),\n]+')
    time = [get_sec(pattern.split(line)[1]) for line in lines_in]
    brightness_R_list, brightness_G_list, brightness_B_list = zip(*[map(float, pattern.split(line)[2:5]) for line in lines_in])
    
    # use different names for different entities
    brightness_R = array(brightness_R_list)
    brightness_G = array(brightness_G_list)
    brightness_B = array(brightness_B_list)
    
    """
    figure(1)
    clf()
    plt1 = subplot(111)
    plot(time, brightness_R, color="red")
    plot(time, brightness_G, color="green")
    plot(time, brightness_B, color="blue")
    show()
    draw()
    savefig("RGB_crappy.png", dpi=400)
    """
    
    time = array(time)
    lightcurve = brightness_B+brightness_G+brightness_R
    
    
    #### 3. EXECUTE EXAMPLE ####
    
    lightcurve_analyze(time, lightcurve, True)

# these two lines are necessary for the main function to be called
# when this script is called from another script, the main function does not 
# execute    
if __name__ == '__main__':
    main()
