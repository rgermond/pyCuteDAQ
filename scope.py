#standard python repository
import logging

#SciPy stack
import matplotlib.pyplot as plt
import numpy as np

class Scope:
    """
    Scope class wraps a matplotlib.pyplot figure and acts as an interactive plotting tool
    """
    def __init__(self, fs, n):
        """
        __init__ - creates and instance of the Scope class, starts the logger
            args:
                fs - (number) - "sampling frequency" of the scope
                n - (int) - number of points in the scope
            returns:
                nothing
        """

        self.logger = logging.getLogger('vib_daq.scope.Scope')
        plt.ion()       #turn interactive plotting on
        self.fig, self.axarr = plt.subplots(3, sharex=True)     #set up subplots

        #setup appearance of figure
        self.fig.suptitle('CUTE Triaxial Accelerometers', fontsize=16, fontweight='bold')
        self.axarr[0].set_title('TAXX', fontsize=14)
        self.axarr[1].set_title('TAXY', fontsize=14)
        self.axarr[2].set_title('TAXZ', fontsize=14)
        self.axarr[1].set_ylabel('Acceleration (g)', fontsize=14)
        self.axarr[2].set_xlabel('Time (s)', fontsize=14)

        #initialize the line objects
        t = np.linspace(0, n/fs, n)
        self.logger.debug('length of t: '+str(len(t)))
        y = np.zeros(n)

        #make line objects
        self.line1, = self.axarr[0].plot(t, y, 'b.')
        self.line2, = self.axarr[1].plot(t, y, 'r.')
        self.line3, = self.axarr[2].plot(t, y, 'g.')

        self.logger.debug('init method executed')

    def draw(self, tp):
        """
        draw - updates the plot with values obtained from the DAQ
            args:
                tp - (tuple) - 3-tuple of arrays of values, the values then get plotted on the corresponding subplot
            returns:
                nothing
        """
        self.logger.debug('length of y1: '+str(len(tp[0])))
        self.logger.debug('length of y2: '+str(len(tp[1])))
        self.logger.debug('length of y3: '+str(len(tp[2])))

        #update the data of the lines
        self.line1.set_ydata(tp[0])
        self.line2.set_ydata(tp[1])
        self.line3.set_ydata(tp[2])

        #update the plot limits
        for ax in self.axarr:
            ax.relim()
            ax.autoscale()

        #redraw the plot space, not window
        self.fig.canvas.draw()
        self.logger.debug('draw method executed')

    def close(self):
        """
        close - closes the plot
            args:
                nothing
            returns:
                nothing
        """
        plt.close()

