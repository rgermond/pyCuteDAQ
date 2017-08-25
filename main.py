#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#standard python repository
import sys, getopt
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

def user_input(daq):
    print('Enter "h" for options')
    while True:
        msg = input('CUTE VibDAQ> ')
        if msg == 'q':
            daq.take_data = False       #stop taking data
            break

        elif msg == 'h':
            input_usage()

        elif msg == 'p':
            print('feature not implemented yet')

        elif msg == 's':
            print('feature not implemented yet')

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

def main(argv):

#----------------    Parse CLi Arguments    ----------------#
    try:
        opts, args = getopt.getopt(argv, 'hsa:p:', ['help','scope','address=','port='])

    except getopt.GetoptError:
        usage()
        sys.exit(2)

    #initialize default args
    address = ''
    port = ''
    scope_on = False

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
    fh = logging.FileHandler('vib_daq.log')
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
    config.read('vib_daq.cfg')

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

    #create the scope
    scope = Scope(daq.fs, daq.n_frames)

    #create daq thread so console input can be received without blocking
    daq_thread = threading.Thread(target=daq.run)
    inpt_thread = threading.Thread(target=user_input,args=(daq,))

    #start the threads
    daq_thread.start()
    inpt_thread.start()

    #where the scope does stuff
    while daq.take_data:

        if scope_on:
            if not q.empty():
                traces = q.get()
                scope.draw(traces)

    #wait for the two threads to complete
    inpt_thread.join()
    daq_thread.join()


if __name__ == '__main__':
    main(sys.argv[1:])
