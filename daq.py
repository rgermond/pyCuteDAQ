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
    The DAQ class sets up the Controller and UDBF classes and allows for the sensors values to be read out
    """

    def __init__(self, address, port, queue, scope_on=False, n_frames=100, n_fft=1e3, n_avg=10, save_raw=False, save_psd=True, convert=None):
        """
        constructs the DAQ class, starts the logger

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
        self.take_data = True
        self.paused = False
        self.scope_on = scope_on
        self.save_raw = save_raw
        self.save_psd = save_psd

        #optional conversion argument, either None or a dict
        self.convert  = convert

        #parameters regarding the number of frames acquired and psd/file size
        self.n_frames = n_frames
        self.n_fft    = n_fft
        self.n_avg    = n_avg

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
        writes the data to CSV files if specified and puts values for the scope in a thread safe queue

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
                if not self.paused:

                    #generate a filename from the current time
                    stamp = time.strftime('%y%m%d_%H%M%S', time.localtime())
                    psdfile = 'psd_fs'+ str(int(self.fs)) + '_' + stamp + '.csv'

                    #initialize dictionary that will hold averaged PSDs
                    psd  = {name:[0 for _ in range(self.n_fft)] for name in self.udbf.var_names[1:]}

                    #loop for the number of averages that are used
                    for avg_ in range(self.n_avg):

                        #make dictionaries for data
                        data = {name:[] for name in self.udbf.var_names}

                        #pause to let the buffer fill up
                        time.sleep(self.n_fft/self.fs)

                        self.logger.info('Acquiring '+ str(int(self.n_fft))+ ' frames of data')

                        frame_count = 0


                        while frame_count < self.n_fft:

                            frame_count += self.n_frames

                            #acquire the buffer
                            buff = self.ctrl.acquire_buffer(self.frame_size, self.n_frames)

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

                            #if the scope is on put the frames in the queue
                            if self.scope_on:
                                tp = (frames['TAXX'],frames['TAXY'],frames['TAXZ'])
                                if all(len(ls)==self.n_frames for ls in tp):
                                    self.queue.put(tp)

                            #save the raw trace
                            if self.save_raw:
                                #generate filename for raw file
                                stamp = time.strftime('%y%m%d_%H%M%S', time.localtime())
                                vibfile = 'vib_fs'+ str(int(self.fs)) + '_' + stamp + '.csv'

                                #write the file
                                dict_writer(vibfile, self.udbf.var_names[1:], data)
                                self.logger.info('Wrote raw trace to csv file: '+ vibfile)

                            #calculate psd here
                            for key in psd:
                                freq, Pxx = welch(data[key], fs=self.fs, nfft=self.n_fft)

                                #loop over each value in the PSD and add it to the avg psd set
                                for idx, val in enumerate(list(Pxx)):
                                    psd[key][idx] += val

                    #divide the PSD values by the number of averages used
                    for key in psd:
                        for idx,val in enumerate(psd[key]):
                            psd[key][idx] = val/self.n_avg

                    #save the PSD
                    if self.save_psd:
                        dict_writer(psdfile, self.udbf.var_names[1:], psd)
                        self.logger.info('Wrote PSD to csv file: '+ psdfile)

        except socket.timeout:
            self.logger.error('socket timed out')
            pass
        except:
            self.logger.error('Unexpected error occurred')
            raise

        finally:
            self.ctrl.close()
            self.logger.info('Data acquisition finished')

