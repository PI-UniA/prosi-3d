import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import sys

from prosi3d.meta.featureExtractor import FeatureExtractor
from prosi3d.sensors.methodsCollection import MethodsCollections

""" Subclass from Abstract Base Class featureExtractor that outputs features of the raw data that are required for machine learning models """
class Accousticplatform(FeatureExtractor):

    """ Accousticplatform is subclass of FeatureExtractor providing the Methods get_data, process, and write.
        
        Attribute: 
            xt:
            yt:
            xf: 
            yf:
            peaks_x:
            peaks_y:
    """


    
    def get_data(self, hdf):
        """ Extract the measurements of the accousticplatform from the hdf5 file
        
        Args:
            hdf: path of the hdf5 file.

        Returns:
            Assign the measurements to the attribute yt and the time values to the attribute xt
        
        Raises:
            IOError: File can not found.
        """
       
        # method to read the hdf5 file
        self._read_measurements(hdf)
        

    def process(self):
        """ Convert the signal of the time domain to a representation in the frequency domain using the rFFT. Identify particularly conspicuous peaks in the frequency domain. """
        
        # method to replace nan values
        self._replace_nan()
        
        # method to shift the x-axis to the mean
        self._move_to_mean()

        # method to create the frequency datas (freqence, power spectral density)
        self._create_FFT()

        # method to find peaks
        peaks = self._find_peaks_values()
        self.peaks_x = np.array([self.xf[peaks[0]]])
        self.peaks_y = np.array([self.yf[peaks[0]]])


    
    def write(self):
        """ Print the x-values and the y-values of the peaks which are saved in to numpy arrays.
        
        """

        print("x-Werte Peaks: ", self.peaks_x)
        print("y-Werte Peaks: ", self.peaks_y)


    """ Abstract method from freatureExtractor to create the time domain """
    def _read_measurements(self, hdf):
        
        # Measurements of the accousticplatform in column 3
        sensorwert = 2 
        self.xt, self.yt = MethodsCollections._read_measurements_C(hdf, sensorwert)


    """ Abstract method from featureExtractor to replace nan values with the mean of the neighboring values """
    def _replace_nan(self): 
        self.yt = MethodsCollections._replace_nan_C(self.yt)
        

    """ Abstract method from featureExtractor to shift the x-axis to the mean """
    def _move_to_mean(self):
        self.yt = MethodsCollections._move_to_mean(self.yt)


    """ Abstract method from featureExtractor to create the rFFT """
    def _create_FFT(self):
        self.xf, self.yf = MethodsCollections._create_FFT_C(self.yt)
        

    """ Abstract method from featureExtractor to find the peaks """
    def _find_peaks_values(self):
        
        try:
            # TODO Parameter müssen noch gewählt werden, siehe https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html
            height = 1*1e-6
            distance = None
            prominence = None

            # return value: index of the peaks
            peaks = find_peaks(self.yf, height, distance, prominence)
            
            return peaks
        
        except:
            raise Exception ("Fehler in der Methode _find_peaks_values() in Klasse Accousticplatform. Fehlertyp: ", sys.exc_info()[0])





    # Nur derzeitig zum Testen enthalten (kann später entfernt werden)
    def plot_test(self):
        """ Plot the diagramms with the identified peaks in order to check the methods 
        
        """
        try:
            fig, ax = plt.subplots(2)
            
        
            # plot time domain
            ax[0].plot(self.xt, self.yt, linewidth=0.1)
            ax[0].set_title('Zeitbereich')
            ax[0].set_xlabel('Zeit in [ms]')
            ax[0].set_ylabel('Sensormesswert')

            # plot frequency domain
            ax[1].scatter(self.xf, self.yf, s=2)
            ax[1].set_title(f'Frequenzbereich')
            ax[1].set_xlabel('Frequenz in [Hz]')
            ax[1].set_ylabel('Spektale Leistungsdichte')
            plt.ylim(-0.0000005, 0.000005) ###Achtung: Wurde angepasst

            # plot peaks
            ax[1].scatter(self.peaks_x, self.peaks_y, marker="x")

            fig.suptitle("Accousticplatform")
            fig.tight_layout()
            plt.show ()
        
        except:
            raise Exception("Fehler in der Methode plot_test der Klasse Accousticplatform. Fehlertyp: ", sys.exc_info()[0])
    