#standard python repository
import time
import logging

#SciPy stack
from scipy.signal import welch

#my classes
from acquire import Controller
from decode import UDBF
from scope import Scope

class   DAQ:

    def __init__(self, address, port, scope_on, n_frames=1000, n_fft=10e3):

        self.logger = logging.getLogger('vib_daq.daq.DAQ')
        self.ctrl = Controller(address,port)
        self.udbf = UDBF()

        self.scope_on = scope_on

        self.n_frames = n_frames
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

                self.logger.info('Acquiring '+ str(int(self.n_fft))+ ' frames of data')

                #make dictionaries for data and psd
                data = {name:[] for name in self.udbf.var_names}
                psd  = {name:[] for name in self.udbf.var_names[1:]}

                #for i in range(int(self.n_fft/self.n_frames)):
                frame_count = 0
                while frame_count < self.n_fft:

                    #pause to let the buffer fill up
                    time.sleep(self.n_frames/self.fs)#

                    #acquire the buffer
                    buff = self.ctrl.acquire_buffer(self.frame_size, self.n_frames)
                    frame_count += self.n_frames

                    #decode the buffer
                    frames = self.udbf.decode_buffer(buff)
                    self.logger.info('Succesfully decoded binary buffer')

                    #add the frames to the data dict
                    #can also potentially do conversion here
                    for key in data:
                        data[key] += frames[key]

                    if self.scope_on:
                        y1 = frames['TAXX']
                        y2 = frames['TAXY']
                        y3 = frames['TAXZ']
                        self.scope.draw(y1, y2, y3)

                #calculate psd here
                for key in psd:
                    freq, psd[key] = welch(data[key], fs=self.fs, nfft=self.n_fft)

                #write to file
                #self.udbf.write_csv(filename)      #write everything but the timestamp
                self.logger.info('Wrote data to csv file: '+ filename)

        #might want to add other except blocks to catch other errors
        except KeyboardInterrupt:
            self.logger.info('Keyboard interrupt signal received')
        except:
            raise
        finally:
            self.ctrl.close()
            self.logger.info('Data acquisition finished')

