#standard python repository
import struct
import logging

class   UDBF:
    """
    The UDBF class decodes the version 1.07 of the Universal Data Bin File format, as specified by Gantner Instruments.
    UDBF provides methods that decodes the various binary streams sent by a Gantner Instruments Q.Gate IP controller,
    Header information is stored in the instance, meaning a call to decode_header must be made before subsequent calls to decode_buffer
    """

    def __init__(self):
        """
        creates and instance of the UDBF class, starts the logger

            args:
                nothing
            returns:
                nothing
        """
        self.logger = logging.getLogger('vib_daq.udbf.UDBF')

    def decode_header(self,raw_head):
        """
        decodes the binary header from the controller

            args:
                raw_head - (bytes) : binary stream
            returns:
                nothing

        """

        self.rh = raw_head
        self.ba = bytearray(raw_head)

        #get endianess and version of binary format
        self.IsBigEndian    = self.ba[0]
        self.Version        = 256*self.ba[1]+self.ba[2]
        self.TypeVendorLen  = 256*self.ba[3]+self.ba[4]

        #if the version of the UDBF file isn't 1.07 raise an error
        if self.Version != 107:
            self.logger.error('UDBF does not support version: ' + str(self.Version))
            raise ValueError('UDBF only supports version 1.07')

        #get the length of the vendor name (should be 43) and make it a string
        #exclude the last character as this is just a trailing \x00
        VenEnd              = 5 + self.TypeVendorLen
        self.TypeVendor     = ''.join([chr(b) for b in self.ba[5:VenEnd-1]])

        #see if theres a checksum at the end and get other decoding info
        self.WithCheckSum   = self.ba[VenEnd]
        self.ModAddDataLen  = 256*self.ba[VenEnd+1] + self.ba[VenEnd+2]
        self.StartTime2DayF = struct.unpack('>d',self.rh[VenEnd+3:VenEnd+11])[0]
        self.dActTimeDataTyp= 256*self.ba[VenEnd+11] + self.ba[VenEnd+12]

        #if there is additional data raise an error, not supported
        if self.ModAddDataLen != 0:
            self.logger.error('UDBF does not support additional data in stream')
            raise ValueError('UDBFheader does not handle additional data in the header file')

        #get other decoding info, including sampling frequency
        self.dActTime2SecF  = struct.unpack('>d',self.rh[VenEnd+13:VenEnd+21])[0]
        self.StartTime      = struct.unpack('>d',self.rh[VenEnd+21:VenEnd+29])[0]
        self.SampleRate     = struct.unpack('>d',self.rh[VenEnd+29:VenEnd+37])[0]

        #number of variables
        self.VarCount       = 256*self.ba[VenEnd+37] + self.ba[VenEnd+38]

        #set up parameters to loop through the variable settings
        VarStart = VenEnd + 39

        #arrays that will be appended to
        self.NameLen        = []
        self.Name           = []
        self.DataDirection  = []
        self.DataType       = []
        self.FieldLen       = []
        self.Precision      = []
        self.UnitLen        = []
        self.Unit           = []
        self.AddDataLen     = []

        #for reach variable
        for var in range(self.VarCount):

            #loop over each variable as specified by VarCount and get the corresponding fields
            #including the name, unit, data type, field length and precision
            nl = self.ba[VarStart]+self.ba[VarStart+1]
            self.NameLen.append(nl)
            self.Name.append(''.join([chr(b) for b in self.ba[VarStart+2:VarStart+nl+1]]))

            self.DataDirection.append(self.ba[VarStart+nl+2]+self.ba[VarStart+nl+3])
            self.DataType.append(self.ba[VarStart+nl+4]+self.ba[VarStart+nl+5])
            self.FieldLen.append(self.ba[VarStart+nl+6]+self.ba[VarStart+nl+7])
            self.Precision.append(self.ba[VarStart+nl+8]+self.ba[VarStart+nl+9])

            ul = self.ba[VarStart+nl+10]+self.ba[VarStart+nl+11]
            self.UnitLen.append(ul)

            self.Unit.append(''.join([chr(b) for b in self.ba[VarStart+nl+12:VarStart+nl+ul+11]]))
            self.AddDataLen.append(self.ba[VarStart+nl+ul+12+self.ba[VarStart+nl+ul+13]])

            #if there is additional data raise an error, not supported
            if self.ModAddDataLen != 0:
                self.logger.error('UDBF does not support additional data in stream')
                raise ValueError('UDBFheader does not handle additional data in the header file')

            VarStart = VarStart + nl + ul + 14

        #make the list of names including the counter
        self.var_names = ['Counter'] + self.Name
        self.var_sizes = [8] + [4 for i in range(self.VarCount)]


    def decode_buffer(self,bs):
        """
        decodes the binary stream from the controller based on information in the header
            args:
                bs - (bytes) : binary stream
            returns:
                data - (dict) : dictionary where keys correspond to sensor names and values are arrays of the sensors' values

        """

        start = 0
        data = {name:[] for name in self.var_names}

        #loop over bytes in the byte array until the end
        while start+sum(self.var_sizes)<= len(bs):
            #for each variable get its size
            for i,size in enumerate(self.var_sizes):

                #determine if it is a double or a float (8 vs 4 bytes)
                if size==8:
                    fmt = '>d'
                elif size==4:
                    fmt = '>f'

                #store the value in the dictionary and update the start position for the next iteration
                data[self.var_names[i]].append(struct.unpack(fmt,bs[start:start+size])[0])
                start += size

        return data

