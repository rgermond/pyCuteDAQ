#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#standard python repository
import sys, getopt
import configparser
import logging

#my classes
from daq import DAQ

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
    ch.setLevel(logging.DEBUG)

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

    #start the DAQ
    daq = DAQ(address, port, scope_on=scope_on, convert=convert)
    logger.info('Starting DAQ')
    daq.start()

if __name__ == '__main__':
    main(sys.argv[1:])
