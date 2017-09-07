#standard python repository
import socket
import logging
import time

class   Controller:
    """
    The Controller class sets up a socket connection and handles communication with the Gantner Q.Gate IP controller

    """

    def __init__(self,address,port):
        """
        constructs a TCP socket using IPv4 protocols with the controller, starts the logger

            args:
                address - (string) : string containing the IPv4 address of the controller, eg. '192.168.1.28'
                port - (int) : port number the controller is on, eg. 10000
            returns:
                nothing
        """

        self.logger = logging.getLogger('vib_daq.controller.Controller')
        self.address = address
        self.port    = port

        #create the socket instance
        self.sckt    = socket.socket()
        self.sckt.settimeout(10)         #set the socket timeout

        try:
            #connect the socket to the appropriate address/port
            self.sckt.connect((self.address,self.port))
            self.logger.info('Connected to Q.Gate at: '+ self.address + ' ' + str(self.port))

        except socket.timeout:
            self.logger.error('Could not connect')
            raise

        #pause for a few seconds so the greeting messages can pileup
        time.sleep(2)

        #read out the greeting messages when the connection is made
        g1 = self.sckt.recv(1024)
        self.logger.info('Received greeting message from Q.Gate')

    def acquire_head(self):
        """
        sends a request to the Gantner controller to provide the binary header, reads out that header, and returns the bytestring
            args:
                nothing
            returns:
                head - (bytes) : bytestring corresponding to binary header, returned from Gantner controller
        """

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
        """
        sends a request over the socket to the Gantner controller to start filling the circular buffer

            args:
                nothing
            returns:
                nothing
        """

        #bytecode to request circular buffer
        bf = b'$RBDC\t0\r'
        #send the request to start receiving the buffer
        self.sckt.send(bf)
        self.logger.info('Requested circular buffer from Q.Gate')

    def acquire_buffer(self,frame_size,n_frames):
        """
        receives the circular buffer data from the controller over the socket

            args:
                frame_size - (int) : number of bytes in a single frame (including timestamp)
                n_frames - (int) : number of frames to read out from the controller, semi arbitrary, eg. 1000

            returns:
                buff - (bytes) : bytestring of length frame_size*n_frames, corresponding to the frames
        """
        #receives n_frames of the given frame_size
        buff = self.sckt.recv(frame_size*n_frames)
        self.logger.info('Received circular buffer from Q.Gate')

        return buff

    def close(self):
        """
        closes the connection with the controller

            args:
                nothing
            returns:
                nothing
        """
        self.sckt.close()
        self.logger.info('Closed TCP socket')
