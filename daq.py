#standard python repository
import time
import logging

#my classes
from acquire import Controller
from decode import UDBF
from scope import Scope

class   DAQ:

    def __init__(self, address, port, scope_on, n_rows=40e3, n_frames=1000, n_fft=10e3):

        self.logger = logging.getLogger('vib_daq.daq.DAQ')
        self.ctrl = Controller(address,port)
        self.udbf = UDBF()

        self.scope_on = scope_on

        self.n_frames = n_frames
        self.n_rows   = n_rows
        self.n_fft    = n_fft

        self.logger.info('Created DAQ successfully')

    def start(self):
        #get the binary header from the controller
        bin_head  = self.ctrl.acquire_head()

        #decode the binary header
        self.udbf.decode_header(bin_head)
        self.logger.info('Succesfully decoded binary header')

        #get sampling frequency
        self.fs = self.udbf.SampleRate

        #initialize the scope if necessary
        if self.scope_on:
            self.scope = Scope(self.fs, self.n_frames)

        #start the circular buffer
        self.ctrl.request_buffer()

        self.frame_size = sum(self.udbf.var_sizes)
        try:
            #loop forever while continually reading out the buffer and decoding the binary stream
            for _ in range(4):

                #generate a filename from the current time
                stamp = time.strftime('%Y%m%d_%H%M%S', time.localtime())
                filename = 'vib_fs'+ str(self.fs) + '_' + stamp + '.csv'

                self.logger.info('Acquiring '+ str(int(self.n_rows))+ ' frames of data')
                for i in range(int(self.n_rows/self.n_frames)):

                    #pause to let the buffer fill up
                    time.sleep(self.n_frames/self.fs)#

                    #acquire the buffer
                    buff = self.ctrl.acquire_buffer(self.frame_size, self.n_frames)

                    #decode the buffer
                    self.udbf.decode_buffer(buff)
                    self.logger.info('Succesfully decoded binary buffer')

                    if self.scope_on:
                        y1 = self.udbf.data['TAXX'][-self.n_frames:]
                        y2 = self.udbf.data['TAXY'][-self.n_frames:]
                        y3 = self.udbf.data['TAXZ'][-self.n_frames:]
                        self.scope.draw(y1, y2, y3)

                #write to file
                self.udbf.write_csv(filename)      #write everything but the timestamp
                self.logger.info('Wrote data to csv file: '+ filename)

        #might want to add other except blocks to catch other errors
        except KeyboardInterrupt:
            self.logger.info('Keyboard interrupt signal received')
        except:
            raise
        finally:
            self.ctrl.close()
            self.logger.info('Data acquisition finished')

