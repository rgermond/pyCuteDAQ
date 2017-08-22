import time

from acquire import QGateController
from decode import UDBF

class   DAQ:


    def __init__(self,address,port):
        self.ctrl = QGateController(address,port)
        self.udbf = UDBF()

        self.n_frames = 10
        self.n_rows   = 40e3

    def start(self):
        #get the binary header from the controller
        bin_head  = self.ctrl.acquire_head()

        #decode the binary header
        self.udbf.decode_header(bin_head)

        #get sampling frequency
        self.fs = self.udbf.SampleRate

        #start the circular buffer
        self.ctrl.request_buffer()

        self.frame_size = sum(self.udbf.var_sizes)
        try:
            #loop forever while continually reading out the buffer and decoding the binary stream
            for _ in range(4):

                #generate a filename from the current time
                stamp = time.strftime('%Y%m%d_%H%M%S', time.localtime())
                filename = stamp + '.csv'

                print('Acquiring ', str(int(self.n_rows)), ' frames of data')
                for i in range(int(self.n_rows/self.n_frames)):

                    #pause to let the buffer fill up
                    time.sleep(self.n_frames/self.fs)#

                    #acquire the buffer
                    buff = self.ctrl.acquire_buffer(self.frame_size, self.n_frames)

                    #decode the buffer
                    self.udbf.decode_buffer(buff)

                #write to file
                self.udbf.write_csv(filename)      #write everything but the timestamp
                print('Wrote data to csv file: ', filename)

        #might want to add other except blocks to catch other errors
        except KeyboardInterrupt:
            pass
        except:
            raise
        finally:
            self.ctrl.close()
            print('Data acquisition finished')

def main():
    #start the DAQ here
    daq = DAQ('192.168.1.28',10000)         #probably change this too so that the IP address can be set through GUI or config file
    daq.start()

if __name__ == '__main__':
    main()
