#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#standard python repository
import sys, getopt
import os
import configparser
import logging
import threading
import queue

#my classes
from daq import DAQ
from scope import Scope

def input_usage():
    print('h : help')
    print('p : pause')
    print('q : quit')
    print('s : toggle scope')
    print('r : toggle save raw')
    print('f : toggle save psd')

def user_input(daq):
    print('Enter "h" for options')
    while True:
        msg = input('CUTE VibDAQ> ')
        if msg == 'q':
            daq.take_data = False       #stop taking data
            break

        elif msg in ['h','?','help']:
            input_usage()

        elif msg == 'p':
            daq.paused = not daq.paused

        elif msg == 'r':
            daq.save_raw = not daq.save_raw

        elif msg == 'f':
            daq.save_psd = not daq.save_psd

        elif msg == 's':
            daq.scope_on = not daq.scope_on

def usage():
    print('Usage: main.py --additional-arguments')
    print()
    print('Note that both long and short format arguments followed by "=" require an additional argument')
    print('Example: main.py -a <IPv4 address> --port <port>')
    print()
    print('Options:')
    print('-h, --help         : display usage')
    print('-a, --address=     : IPv4 address of Q.Gate')
    print('-p, --port=        : should be 10000')
    print('-s, --scope        : turn scope functionality on')


def main():
    """
    Main file to be executed for the vibration DAQ used for CUTE
    It imports the DAQ and Scope classes and modifies their behaviour using multiple threads
    This file handles path related things so that the script can be called and the appropriate configuration and log files are found.
    It parses command line arguments that can modify the DAQ and Scope functionality
    It creates the DAQ object, starts its run method in a seperate thread.
    Passes the DAQ object to the user_input function and starts that process in another thread.
    The Scope object is managed in the main thread as GUI components must be in the main thread.
    When the quit option is passed to the main thread all the threads join.
    """

#----------------    Path Related Things    ----------------#

    #make the relavent full paths
    cwd = os.getcwd()
    daq_path = sys.path[0]
    data_path = os.path.join(daq_path, 'data')
    vib_path = os.path.join(data_path, 'vib')
    psd_path = os.path.join(data_path, 'psd')

    #create the paths if they dont already exist
    if not os.path.exists(data_path):
        os.mkdir(data_path)
    if not os.path.exists(vib_path):
        os.mkdir(vib_path)
    if not os.path.exists(psd_path):
        os.mkdir(psd_path)

#----------------    Parse CLi Arguments    ----------------#

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hsa:p:', ['help','scope','address=','port='])

    except getopt.GetoptError:
        usage()
        sys.exit(2)

    #initialize default args
    address = ''
    port = ''
    scope_on = False
    scope = None

    #loop through all of the arguments
    for opt, arg in opts:

        #help option
        if opt in ('-h','--help'):
            usage()
            sys.exit(0)

        #address option
        elif opt in ('-a','--address'):
            address = arg

        #port option
        elif opt in ('-p','--port'):
            try:
                port = int(arg)
            except:
                raise

        #scope functionality option
        elif opt in ('-s','--scope'):
            scope_on = True

#-----------------    Setup the Logger    -----------------#

    #create logger
    logger = logging.getLogger('vib_daq')
    logger.setLevel(logging.DEBUG)

    #create file handler
    log_file = os.path.join(daq_path,'vib_daq.log')
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    #create stream handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)

    #create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    #add formatter to the handlers
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    #add handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

#-----------------    Read Config File    -----------------#

    #set up config parser
    config = configparser.ConfigParser()
    config.optionxform = str    #preserve case on import
    cfg_file = os.path.join(daq_path,'vib_daq.cfg')
    config.read(cfg_file)

    #conversion parameters
    convert = None
    if 'convert' in config.sections():
        convert = {key:config['convert'].getfloat(key) for key in config['convert']}

    #network parameters
    if not address:
        address = config['network'].get('IPv4')
    if not port:
        port = config['network'].getint('Port')

#-----------------    Start the DAQ    -----------------#

    #create queue for the scope
    q = queue.Queue()

    #create DAQ instance
    daq = DAQ(address, port, q, scope_on=scope_on, convert=convert)

    #create daq thread so console input can be received without blocking
    daq_thread = threading.Thread(target=daq.run)
    inpt_thread = threading.Thread(target=user_input,args=(daq,))

    #start the threads
    daq_thread.start()
    inpt_thread.start()

#-----------------    Control Scope    -----------------#

    while daq.take_data:

        if daq.scope_on:

            if scope is None:
                #create the scope
                scope = Scope(daq.fs, daq.n_frames)

            if not q.empty():
                traces = q.get()
                scope.draw(traces)
        else:
            if scope is not None:
                scope.close()
                scope = None

#-----------------    Join Threads    -----------------#

    #wait for the process to complete, blocks the main process
    inpt_thread.join()
    daq_thread.join()

#-----------------    Clean Up Files    -----------------#

    #loop through the files in the daq directory, moving csv files with the correct formatting to the data directory
    files = os.listdir(cwd)
    for f in files:
        if f.startswith('vib_') and f.endswith('.csv'):
            src = os.path.join(cwd,f)
            dst = os.path.join(vib_path,f)
            os.rename(src,dst)
        elif f.startswith('psd_') and f.endswith('.csv'):
            src = os.path.join(cwd,f)
            dst = os.path.join(psd_path,f)
            os.rename(src,dst)

if __name__ == '__main__':
    main()
