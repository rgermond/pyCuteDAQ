#standard python repository
import time
import csv
import logging

#SciPy stack
from scipy.signal import welch

#my classes
from acquire import Controller
from decode import UDBF

def dict_writer(filename, headers, data):
    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()

        while any(data[headers[0]]):
            try:
                d = {header:data[header].pop(0) for header in headers}
                writer.writerow(d)

            except IndexError:
                break
            except:
                raise

class   DAQ:

    def __init__(self, address, port, queue, scope_on=False, n_frames=100, n_fft=1e3, save_raw=False, save_psd=False, convert=None):

        self.logger = logging.getLogger('vib_daq.daq.DAQ')
        self.ctrl = Controller(address,port)
        self.udbf = UDBF()

        #queue for storing the data
        self.queue = queue

        #boolean options which dictate behaviour of DAQ
        self.take_data= True
        self.scope_on = scope_on
        self.save_raw = save_raw
        self.save_psd = save_psd

        #optional conversion argument, either None or a dict
        self.convert  = convert

        #parameters regarding the number of frames acquired and psd/file size
        self.n_frames = n_frames
        self.n_fft    = n_fft

        self.logger.info('Created DAQ successfully')

        #get the binary header from the controller
        bin_head  = self.ctrl.acquire_head()

        #decode the binary header
        self.udbf.decode_header(bin_head)
        self.logger.info('Succesfully decoded binary header')

        #get sampling frequency
        self.fs = self.udbf.SampleRate


    def run(self):
        #start the circular buffer
        self.ctrl.request_buffer()

        self.frame_size = sum(self.udbf.var_sizes)
        try:
            #loop until user specifies to end
            while self.take_data:

                #generate a filename from the current time
                stamp = time.strftime('%Y%m%d_%H%M%S', time.localtime())
                vibfile = 'vib_fs'+ str(self.fs) + '_' + stamp + '.csv'
                psdfile = 'psd_fs'+ str(self.fs) + '_' + stamp + '.csv'

                self.logger.info('Acquiring '+ str(int(self.n_fft))+ ' frames of data')

                #make dictionaries for data and psd
                data = {name:[] for name in self.udbf.var_names}
                psd  = {name:[] for name in self.udbf.var_names[1:]}

                #pause to let the buffer fill up
                #time.sleep(self.n_fft/self.fs)

                #for i in range(int(self.n_fft/self.n_frames)):
                frame_count = 0
                while frame_count < self.n_fft:

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
                            self.logger.debug('Converted values: '+key)
                        data[key] += frames[key]

                    if self.scope_on:
                        tp = (frames['TAXX'],frames['TAXY'],frames['TAXZ'])
                        if all(len(ls)==self.n_frames for ls in tp):
                            self.queue.put(tp)

                #calculate psd here
                for key in psd:
                    freq, Pxx = welch(data[key], fs=self.fs, nfft=self.n_fft)
                    psd[key] = list(Pxx) #convert to python list

                #save the PSD
                if self.save_psd:
                    dict_writer(psdfile, self.udbf.var_names[1:], psd)
                    self.logger.info('Wrote PSD to csv file: '+ psdfile)

                #save the raw trace
                if self.save_raw:
                    dict_writer(vibfile, self.udbf.var_names[1:], psd)
                    self.logger.info('Wrote raw trace to csv file: '+ vibfile)

        except:
            self.logger.error('Unexpected error occurred')
            raise

        finally:
            self.ctrl.close()
            self.logger.info('Data acquisition finished')

