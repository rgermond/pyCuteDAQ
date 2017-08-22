import sys, getopt
from daq import DAQ

def main(argv):
    try:
        opts, args = getopt.getopt(argv, 'hsa:p:')
    except getopt.GetoptError:
        print('Usage: main.py -a <address> -p <port> --extras')
        sys.exit(2)

    scope_on = False

    for opt, arg in opts:

        #help option
        if opt == '-h':
            print('Usage: main.py -a <address> -p <port> --additional arguments')
            print()
            print('Additional arguments:')
            print('h    -help')
            print('s    -scope functionality on')
            sys.exit(0)

        #address option
        elif opt == '-a':
            address = arg

        #port option
        elif opt == '-p':
            try:
                port = int(arg)
            except:
                raise

        #scope functionality option
        elif opt == '-s':
            scope_on = True

    daq = DAQ(address, port, scope_on)
    daq.start()

if __name__ == '__main__':
    main(sys.argv[1:])
