#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#standard python repository
import sys, getopt
import logging

#my classes
from daq import DAQ

def usage():
    print('Usage: main.py -a <address> -p <port> --additional arguments')
    print()
    print('Required arguments:')
    print('-a, --address    : IPv4 address of Q.Gate')
    print('-p, --port       : should be 10000')
    print()
    print('Additional arguments:')
    print('-h, --help       : display usage')
    print('-s, --scope      : turn scope functionality on')

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
    scope = False

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
            scope = True

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

    if address and port:
        daq = DAQ(address, port, scope_on=scope)
        logger.info('Starting DAQ')
        daq.start()
    else:
        logger.error('No address/port supplied')

if __name__ == '__main__':
    main(sys.argv[1:])
