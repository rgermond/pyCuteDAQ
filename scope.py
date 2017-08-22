import matplotlib.pyplot as plt
import numpy as np

class TAXScope:
    def __init__(self, fs, n):
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
        y = np.zeros(n)

        self.line1, = self.axarr[0].plot(t, y, 'b.')
        self.line2, = self.axarr[1].plot(t, y, 'r.')
        self.line3, = self.axarr[2].plot(t, y, 'g.')

    def draw(self, y1, y2, y3):
        self.line1.set_ydata(y1)
        self.line2.set_ydata(y2)
        self.line3.set_ydata(y3)
        self.fig.canvas.draw()

