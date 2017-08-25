#standard python repository
import logging

#SciPy stack
import matplotlib.pyplot as plt
import numpy as np

class Scope:
    def __init__(self, fs, n):
        self.logger = logging.getLogger('vib_daq.scope.Scope')
        plt.ion()
        self.fig, self.axarr = plt.subplots(3, sharex=True)

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

        self.line1, = self.axarr[0].plot(t, y, 'b.')
        self.line2, = self.axarr[1].plot(t, y, 'r.')
        self.line3, = self.axarr[2].plot(t, y, 'g.')

        self.logger.debug('init method executed')

    def draw(self, tp):
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

        self.fig.canvas.draw()
        self.logger.debug('draw method executed')

