#standard python repository
import socket
import logging
import time

class   Controller:

    def __init__(self,address,port):

        self.logger = logging.getLogger('vib_daq.acquire.Controller')
        self.address = address
        self.port    = port

        #create the socket instance
        self.sckt    = socket.socket()
        self.sckt.settimeout(10)         #set the socket timeout

        #connect the socket to the appropriate address/port
        self.sckt.connect((self.address,self.port))
        self.logger.info('Connected to Q.Gate at: '+ self.address + ' ' + str(self.port))

        #pause for a few seconds so the greeting messages can pileup
        time.sleep(2)

        #read out the greeting messages when the connection is made
        g1 = self.sckt.recv(1024)
        self.logger.info('Received greeting message from Q.Gate')

    def acquire_head(self):

        #bytecode command to acquire circular buffer header
        hd = b'$RBH\r'
        #send the request to read the header
        self.sckt.send(hd)
        self.logger.info('Requested binary header from Q.Gate')

        #receive the response from the controller
        head = self.sckt.recv(1024)
        self.logger.info('Received binary header from Q.Gate')

        return head

    def request_buffer(self):

        #bytecode to request circular buffer
        bf = b'$RBDC\t0\r'
        #send the request to start receiving the buffer
        self.sckt.send(bf)
        self.logger.info('Requested circular buffer from Q.Gate')

    def acquire_buffer(self,frame_size,n_frames):
        #receives n_frames of the given frame_size
        buff = self.sckt.recv(frame_size*n_frames)
        self.logger.info('Received circular buffer from Q.Gate')

        return buff

    def close(self):
        self.sckt.close()
        self.logger.info('Closed TCP socket')
