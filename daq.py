#standard python repository
import time
import csv
import logging

#SciPy stack
from scipy.signal import welch

#my classes
from acquire import Controller
from decode import UDBF
from scope import Scope

def dict_writer(filename, headers, data):
    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()

        while data[headers[0]]:
            try:
                d = {header:data[header].pop(0) for header in headers}
                writer.writerow(d)

            except IndexError:
                break
            except:
                raise

class   DAQ:

    def __init__(self, address, port, scope_on=False, n_frames=1000, n_fft=10e3, save_raw=False, save_psd=True, convert=None):

        self.logger = logging.getLogger('vib_daq.daq.DAQ')
        self.ctrl = Controller(address,port)
        self.udbf = UDBF()

        #boolean options which dictate behaviour of DAQ
        self.scope_on = scope_on
        self.save_raw = save_raw
        self.save_psd = save_psd

        #optional conversion argument, either None or a dict
        self.convert  = convert

        #parameters regarding the number of frames acquired and psd/file size
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
                vibfile = 'vib_fs'+ str(self.fs) + '_' + stamp + '.csv'
                psdfile = 'psd_fs'+ str(self.fs) + '_' + stamp + '.csv'

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
                    for key in data:

                        #do the conversion if convert dict provided
                        if self.convert and self.convert[key]:
                            frames[key] = [self.convert[key]*val for val in frames[key]]
                            self.logger.debug('Converted values: ',+key)
                        data[key] += frames[key]


                    if self.scope_on:
                        y1 = frames['TAXX']
                        y2 = frames['TAXY']
                        y3 = frames['TAXZ']
                        self.scope.draw(y1, y2, y3)

                #calculate psd here
                for key in psd:
                    freq, psd[key] = welch(data[key], fs=self.fs, nfft=self.n_fft)

                #save the PSD
                if self.save_psd:
                    dict_writer(psdfile, self.udbf.var_names[1:], psd)
                    self.logger.info('Wrote PSD to csv file: '+ psdfile)

                #save the raw trace
                if self.save_raw:
                    dict_writer(vibfile, self.udbf.var_names[1:], psd)
                    self.logger.info('Wrote raw trace to csv file: '+ vibfile)

        #might want to add other except blocks to catch other errors
        except KeyboardInterrupt:
            self.logger.info('Keyboard interrupt signal received')
        except:
            raise
        finally:
            self.ctrl.close()
            self.logger.info('Data acquisition finished')

