# CuteDAQ 

## Introduction

This code includes several classes that can be used to acquire data from a Gantner Q.Gate controller over a TCP socket and writes the data to a csv file. It was written for use with the vibration measurement system in the Cryogenic Underground TEst facility (CUTE), a particle astrophysics experiment based out of SNOLAB in Sudbury, ON, ran by SuperCDMS.

The computer should be connected via ethernet to the Gantner Q.Gate IP controller, which is attached to Gantner Q.Bloxx A111 modules that the accelerometers plug in to. The code sets up a TCP socket with the controller, starts the acquisition with a bytecode command, and then continually reads out and decodes the binary streams. The sensor values can be given an optional conversion (using the configuration file), and the PSD is calculated from the time series data and stored to a CSV file (the raw traces can also be optionally stored as well). 

Currently the DAQ only supports UDBF (Universal Data Bin Format) 1.07 and doesn't support additional data to be included in the stream (reference the Gantner QGate manual for more information).

## Prerequisites
The DAQ is written almost entirely using the python3 standard library (except for a few common packages used for the scope and the FFT). Install python3 -if not already on the system- through the package manager or by visiting: https://www.python.org/downloads/. Example on OSX:
```
brew install python3
```
Please note that while the DAQ should be compatible with all systems, it has only ever been tested on Linux and OSX. Python should include its own package manager 'pip', which can be used to install the remaining dependencies. The remaining dependencies are numpy and matplotlib, which can be installed with:
```
pip3 install numpy matplotlib
```
Note that numpy and matplotlib make up the core components of the SciPy stack, a set of packages that are useful for scientific calculations, more details can be found at: https://www.scipy.org/stackspec.html.   

## Installation
Since the DAQ is written in python, nothing needs to be compiled to run. To install simply download or clone the entire DAQ directory to a user writable directory. Example of cloning (using git) the DAQ into a directory called 'vib_daq':    
```
git clone https://github.com/rgermond/pyCuteDAQ.git vib_daq 
```

## Getting Started
The DAQ can be ran from the command line by: 
```
python3 main.py
```
Or if on a UNIX like system:
```
/path/to/vib_daq/main.py
```
Note the above method first requires making the main.py file executable, which on a UNIX like system can be done by:
```
chmod +x main.py
```
The DAQ also supports optional command line parameters to be passed (such as starting the scope automatically), to view a full list of command line options use:
```
/path/to/vib_daq/main.py --help
```
Note that while the IP address and port can be set with a command line argument, they are set by defulat using the included configuration file.
Upon starting the DAQ succesfully, an interactive prompt like the one below will appear:
```
CUTE VibDAQ> 
```
This prompt is used to control the state of the DAQ during operation. It is used to terminate the DAQs execution, and can do things like toggle the scope on and off. To see a list of commands that can be used, type 'h' or '?' or 'help' at the prompt and press enter.

## Features
The DAQ includes the following features:
* Application wide logging to: 'vib_daq.log'
* Configuration file for some settings: 'vib_daq.cfg'
* Interactive prompt during operation
* Scope functionality for certain channels

## Help
The documentation for each function is found within the class. The python help feature can be used to inspect the objects by calling the help.py script with the interactive interpreter flag:
```
python3 -i help.py
```
And then at the python interpreter use:
```
>>> help(DAQ)               #help with DAQ class
>>> help(Scope)             #help with Scope class
>>> help(Controller)        #help with Controller class
>>> help(UDBF)              #help with UDBF class
>>> help(main)              #help with main executable
```

