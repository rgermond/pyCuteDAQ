# CuteDAQ 

## Data Acquisition Controller for Gantner Q. Gate

This code includes several classes that can be used to acquire data from a Gantner Q.Gate controller over a TCP socket and writes the data to a csv file. It was written for use with the vibration measurement system in the Cryogenic Underground TEst facility (CUTE), a particle astrophysics experiment based out of SNOLAB in Sudbury, ON, ran by SuperCDMS.

This code allows for data to be read out from Gantner Q.Gate DAQ over an ethernet port by opening a TCP socket with the controller.
The binary header is read out from the controller and decoded in order to decode the buffer.
The circular buffer begins filling and the data is stored to a CSV file.

Currently the DAQ only supports UDBF (Universal Data Bin Format) 1.07 and doesn't support additional data to be included in the stream (reference the Gantner QGate manual for more information).

## Requirements
The implementation is written using the standard python3 library and the SciPy stack (specifically matplotlib and numpy). 
Although it should be backwards compatible with python2 this hasn't been tested.

## Usage 

To run the code with the default settings (from the configuration file) simply use:
```
python3 main.py
```

To see optional arguments, eg. scope functionality:
```
python3 main.py -h
```

## Things to do

* improve the PSD calculation (using welch method from scipy.signal)
* add some way of breaking out from the main loop cleanly?
* include cli arguments to save raw traces
* output the full csv files to a different directory? 
