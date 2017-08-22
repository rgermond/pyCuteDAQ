#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import struct
import csv

class   UDBF:

    def __init__(self):
        pass

    def decode_header(self,raw_head):
        #this function decodes the binary header
        self.rh = raw_head
        self.ba = bytearray(raw_head)

        #get endianess and version of binary format
        self.IsBigEndian    = self.ba[0]
        self.Version        = 256*self.ba[1]+self.ba[2]
        self.TypeVendorLen  = 256*self.ba[3]+self.ba[4]

        #if the version of the UDBF file isn't 1.07 raise an error
        if self.Version != 107:
            print(self.Version)
            raise ValueError('UDBFheader only supports version 1.07')

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
            raise ValueError('UDBFheader does not handle additional data in the header file')

        #get other decoding info, including sampling frequency
        self.dActTime2SecF  = struct.unpack('>d',self.rh[VenEnd+13:VenEnd+21])[0]
        self.StartTime      = struct.unpack('>d',self.rh[VenEnd+21:VenEnd+29])[0]
        self.SampleRate     = struct.unpack('>d',self.rh[VenEnd+29:VenEnd+37])[0]

        #number of variables
        self.VarCount       = 256*self.ba[VenEnd+37] + self.ba[VenEnd+38]

        #set up parameters to loop through the variable settings
        VarStart = VenEnd + 39

        self.NameLen        = []
        self.Name           = []
        self.DataDirection  = []
        self.DataType       = []
        self.FieldLen       = []
        self.Precision      = []
        self.UnitLen        = []
        self.Unit           = []
        self.AddDataLen     = []

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
                raise ValueError('UDBFheader does not handle additional data in the header file')

            VarStart = VarStart + nl + ul + 14

        #make the list of names including the counter
        self.var_names = ['Counter'] + self.Name
        self.var_sizes = [8] + [4 for i in range(self.VarCount)]

        self.data      = {}
        for name in self.var_names:
            self.data[name] = []

    def decode_buffer(self,bs):
        #this function decodes the binary file
        #takes the binary stream, bs and decodes it based on the number of variables and the frame size

        start = 0
        while start+sum(self.var_sizes)<= len(bs):
            for i,size in enumerate(self.var_sizes):

                #determine if it is a double or a float (8 vs 4 bytes)
                if size==8:
                    fmt = '>d'
                elif size==4:
                    fmt = '>f'

                #store the value in the dictionary and update the start position for the next iteration
                self.data[self.var_names[i]].append(struct.unpack(fmt,bs[start:start+size])[0])
                start += size

    def write_csv(self, filename):

        with open(filename,'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.var_names)
            writer.writeheader()

            while self.data[self.var_names[0]]:
                row = {}
                for key in self.var_names:
                    row[key] = self.data[key].pop(0)

                writer.writerow(row)
