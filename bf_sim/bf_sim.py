# +FHDR-------------------------------------------------------------------------
# FILE NAME      : bf_sim.py
# AUTHOR         : Sammy Carbajal
# ------------------------------------------------------------------------------
# PURPOSE
#   Simulation of a discrete-time beamformer using PDM modulated sensors.
# -FHDR-------------------------------------------------------------------------

import numpy as np
import argparse
from bf_time_sim import *
from bf_freq_1fft_sim import *

def main():

  # ==============================================================================
  #                           ARGUMENTS PARSING
  # ==============================================================================
  
  parser = argparse.ArgumentParser(
             description = "Discrete-time beamformer model (uniform linear array)",
             formatter_class=argparse.ArgumentDefaultsHelpFormatter
                          )
  
  # Array Maximum frequency
  parser.add_argument("--max-array-freq", type=float,
                              default=20e3,
                              help="array maximum frequency in Hertz")
  
  # Input sampling frequency
  parser.add_argument("--inp-samp-freq", type=float,
                              default=3.072e6,
                              help="input sampling frequency in Hertz")

  # Decimator disable
  parser.add_argument("--dec-disable", action='store_true', 
                              help="disable decimation filter")

  # Output sampling frequency
  parser.add_argument("--out-samp-freq", type=float,
                              default=48e3,
                              help="output sampling frequency in Hertz")
  
  # Sound speed
  parser.add_argument("-c", "--sound-speed", type=float,
                              default=340.,
                              help="sound speed in m/s")
  
  # Distance between sensors
  parser.add_argument("-d", "--distance", type=float,
                              help="sensor distance in meters")
  
  # Window length
  parser.add_argument("-D", "--window-length", type=int,
                              default=4,
                              help="input window length in ms")
  
  # Number of sensors
  parser.add_argument("-m", "--num-sensors", type=int,
                              default=50,
                              help="number of sensors")
  
  # Number of frames
  parser.add_argument("-L", "--num-frames", type=int,
                              default=1,
                              help="number of frames")
  
  # Number of angles (directions) tested
  parser.add_argument("-n","--num-angle-pts", type=int,
                              default=180,
                              help="number of angles (directions) tested")
  
  # Arriving sources' angles
  parser.add_argument("-a", "--angles", nargs='+', type=float, 
                              default=[110, 60, 20],
                              help="arriving sources' angles in degrees")
  
  # Arriving sources' frequencies
  parser.add_argument("-f", "--frequencies", nargs='+', type=float,
                              default=[1e3, 3e3, 5e3],
                              help="arriving sources' frequencies in Hertz")
  
  # Arriving sources' amplitudes
  parser.add_argument("-x", "--amplitude", nargs='+', type=float,
                              default=[1.0, 1.0, 1.0],
                              help="arriving sources' relative amplitudes ")
  
  # Sensor noise std dev
  parser.add_argument("--noise-stdv", type=float, default=2.0,
                              help="sensor noise standard deviation in units")
  
  # CIC disable
  parser.add_argument("--cic-disable", action='store_true', 
                              help="disable CIC filter")
  
  # CIC config
  parser.add_argument("--cic-config", nargs=2, type=int, default=[64, 5],
                              help="CIC configuration [CICOSR, ORDER]")
  
  # Plot
  parser.add_argument("-p", "--plot", action="store_true", default=False,
                              help="plot input source data")
  
  # Verbose
  parser.add_argument("-v", "--verbose", action="store_true", default=False,
                              help="increase output verbosity")
  
  # Plot delay
  parser.add_argument("--plot-del-angle", type=int,
                              help="plot delay angle in degrees")
  
  # Save plot
  parser.add_argument("-s","--save-plot-prefix", 
                              help="prefix to save plots")

  # Type
  parser.add_argument("--method", type=str, default='time',
                              help="Domain (time, freq_1fft, freq_2fft, hadam)")

  
  
  args = parser.parse_args()
  
  # ==============================================================================
  #                              SETTING PARAMETERS
  # ==============================================================================
  
  # Sound speed
  c = args.sound_speed
  
  # Distance between sensors
  if args.distance is None:
    B = args.max_array_freq
    d = c/(2*B)
  else:
    d = args.distance
    B = c/(2.*d) 
  
  # Wave number absolute value
  k_abs_max = 2.*np.pi*B/c

  # Decimator disable
  dec_disable = args.dec_disable

  # CIC disable
  cic_disable = args.cic_disable
  
  # CIC OSR
  if not cic_disable:
    cic_osr = args.cic_config[0]
  else:
    cic_osr = 1
  
  # CIC order
  cic_order = args.cic_config[1]

  # Prefix to save plot
  save_plot_prefix = args.save_plot_prefix 
  
  
  # Input sampling frequency
  fsi = args.inp_samp_freq
  
  # Output sampling frequency
  fso = args.out_samp_freq

  # OSR
  OSR = np.ceil(fsi/fso).astype(int)

  # Comp OSR
  comp_osr = OSR/cic_osr
  
  # Window length (input)
  window_length = args.window_length
  Di = np.ceil(window_length*1e-3*fsi).astype(int)
  
  # Number of sensors
  M = args.num_sensors
  
  # Number of frames
  L = args.num_frames
  
  # Angle number of points
  angle_num_pts = args.num_angle_pts
  
  # Plot
  plot = args.plot
  
  # Verbose
  verbose = args.verbose
  
  # Plot delay
  if args.plot_del_angle is not None:
    plot_del =  True
    plot_del_k = args.plot_del_angle
  else:
    plot_del = False
    plot_del_k = 0
  
  # Arriving angles
  angle_deg = np.array(args.angles)  
  angle = angle_deg*np.pi/180.
  
  # Input frequencies
  f_in = np.array(args.frequencies)
  
  # Amplitude
  amp = np.array(args.amplitude)
  
  # Sensor noise 
  stdv = args.noise_stdv
  mean = 0.0
  
  # Maximum delay
  tdel_max = M*d/c
  
  # Maximum delay units
  if dec_disable:
    ndel_max = np.round(tdel_max*fsi).astype(int)
  else:
    ndel_max = np.round(tdel_max*fso).astype(int)

  # Printing
  print 'Array parameters:'
  print '  {0:30}: {1:}'.format('Array type', 'ULA')
  print '  {0:30}: {1:2}'.format('Sensors distance (mm)', d*1e3)
  print '  {0:30}: {1:2}'.format('Number of sensors', M)
  print '  {0:30}: {1:2}'.format('Maximum frequency (KHz)', B/1e3)
  
  print 'Input parameters:'
  print '  {0:30}: {1:}'.format('Sampling frequency (KHz)', fsi/1e3)
  print '  {0:30}: {1:}'.format('Window length (ms)', window_length)
  print '  {0:30}: {1:}'.format('Number of samples', Di)
  print '  {0:30}: {1:}'.format('Sources directions (degrees)', angle_deg)
  print '  {0:30}: {1:}'.format('Sources frequencies (KHz)', f_in/1e3)
  print '  {0:30}: {1:}'.format('Sources amplitude (un)', amp)
  print '  {0:30}: {1:}'.format('Channel noise (stdv) (mean=0)', stdv)
  print '  {0:30}: {1:}'.format('Overall oversampling rate', OSR)
  
  if not cic_disable:
    print 'CIC filter parameters:'
    print '  {0:30}: {1:}'.format('Order', cic_order)
    print '  {0:30}: {1:}'.format('Oversampling rate', cic_osr)
  
  print 'Other parameters:'
  print '  {0:30}: {1:}'.format('Number of frames', L)
  print '  {0:30}: {1:}'.format('Wave number (Hz*s/m)', k_abs_max)
  print '  {0:30}: {1:}'.format('Maximum delay (us)', tdel_max/1e-6)
  print '  {0:30}: {1:}'.format('Maximum delay units ', ndel_max)
  print '  {0:30}: {1:}'.format('Num. tested angles', angle_num_pts)
  print '  {0:30}: {1:}'.format('Sound speed (m/s)', c)
  
  if args.method == 'time':
    bf_time_sim (c, d, cic_osr, cic_disable, cic_order, dec_disable, fsi, fso, 
      OSR, Di, M, angle_num_pts, plot, verbose, plot_del, plot_del_k, angle, 
      f_in, amp, stdv, mean, ndel_max, L, save_plot_prefix) 
  elif args.method == 'freq_1fft':
    bf_freq_1fft_sim (c, d, cic_osr, cic_disable, cic_order, dec_disable, fsi, 
      fso, OSR, Di, M, angle_num_pts, plot, verbose, plot_del, plot_del_k,
      angle, f_in, amp, stdv, mean, ndel_max, L, save_plot_prefix) 
  else:
    print 'Domain \''+ args.method+ '\' not implemented yet.' 
 
if __name__ == '__main__':
  main() 
