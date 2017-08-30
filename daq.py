#standard python repository
import time
import csv
import logging

#SciPy stack
from scipy.signal import welch

#my classes
from controller import Controller
from udbf import UDBF

def dict_writer(filename, headers, data):
    """
    writes a dictionary of values to a csvfile
        args:
            filename - (string) : name of the file to write the data to
            headers - (list) : array of strings of the key names to write to file, in the order of columns
            data - (dict) : dictionary where keys are strings, and values are array of values to be written to file
        returns:
            nothing

    """
    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()

        #while there is data in the first column
        while any(data[headers[0]]):
            try:
                #make a dictionary containing the row
                d = {header:data[header].pop(0) for header in headers}
                writer.writerow(d)

            except IndexError:
                #unless the array is empty, break the while loop
                break
            except:
                #any other errors raise normally
                raise

class   DAQ:
    """
    The DAQ class sets up the Controller and UDBF classes and allows for the sensors to be read out, and their values to be read out
    """

    def __init__(self, address, port, queue, scope_on=False, n_frames=100, n_fft=1e3, save_raw=False, save_psd=True, convert=None):
        """
        creates and instance of the DAQ class, starts the logger
            args:
                address - (string) : string containing the IPv4 address of the controller, eg. '192.168.1.28'
                port - (int) : port number the controller is on, eg. 10000
                queue - (Queue) : queue object to write the data to in a thread safe way
                n_frames - (int) : number of frames to acquire each time the circular buffer is read out
                n_fft - (int) : number of frames in each PSD and CSV file
                scope_on - (bool) : boolean flag to specify if the scope is being used, if so puts the decoded frames in the queue
                save_raw - (bool) : boolean flag to specify if the raw traces (converted if conversions provided) are saved to a CSV file
                save_psd - (bool) : boolean flag to specify if the psd (converted if conversions provided) are saved to a CSV file
                convert - (None or dict) : optional parameter to pass that gives a conversion for variables if the key matches the controller
            returns:
                nothing
        """

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
        """
        starts the daq by requesting the circular buffer, then continually reading it out until the take_data flag is False
              also writes the data to CSV files if specified and puts values for the scope in a thread safe queue
            args:
                nothing
            returns:
                nothing
        """
        #start the circular buffer
        self.ctrl.request_buffer()

        self.frame_size = sum(self.udbf.var_sizes)
        try:
            #loop until user specifies to end
            while self.take_data:

                #generate a filename from the current time
                stamp = time.strftime('%y%m%d_%H%M%S', time.localtime())
                vibfile = 'vib_fs'+ str(int(self.fs)) + '_' + stamp + '.csv'
                psdfile = 'psd_fs'+ str(int(self.fs)) + '_' + stamp + '.csv'

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

        except socket.timeout:
            self.logger.error('socket timed out')
            pass
        except:
            self.logger.error('Unexpected error occurred')
            raise

        finally:
            self.ctrl.close()
            self.logger.info('Data acquisition finished')

