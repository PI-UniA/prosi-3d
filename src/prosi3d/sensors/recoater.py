""" Subclass from Abstract Base Class featureExtractor that outputs features of the raw data that are required for machine learning models """

import numpy as np
import matplotlib.pyplot as plt
import h5py as h5
import sys
from scipy.signal import find_peaks
import math

from prosi3d.meta.featureExtractor import FeatureExtractor
from prosi3d.sensors._methodsCollection import _MethodsCollections

class Recoater(FeatureExtractor):

    """ 
    Attribute: 
        peaks_x (numpy.array): frequency of the peaks.
        
        peaks_y (numpy.array): spectral power density of the peaks.
    """
    
    def get_data(self, hdf):
        """ Extract the measurements of the recoater sensor from the hdf5 file. 
        
        Args:
            hdf (String): path of the hdf5 file.

        Raises:
            IOError: File can not found.
        """
       
        # method to read teh hdf5 file
        self._read_measurements(hdf)
        

    
    def process(self):
        """ Convert the signal of the time domain to the representation in the frequency domain using the rFFT. Identify particularly conspicuous peaks in the frequency domain. """
        
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
        """ Print the x-values and the y-values of the peaks (frequency domain) which are saved in numpy arrays. """

        print("x-Werte Peaks: ", self.peaks_x)
        print("y-Werte Peaks: ", self.peaks_y)


    # Abstract method from freatureExtractor to create the time domain
    def _read_measurements(self, hdf):
        
        # Measurements of the recoater in column 4
        sensorwert = 3
        self.xt, self.yt = _MethodsCollections._read_measurements_C(hdf, sensorwert)


    # Abstract method from featureExtractor to replace nan values with the mean of the neighboring values
    def _replace_nan(self): 
        self.yt = _MethodsCollections._replace_nan_C(self.yt)
        

    # Abstract method from featureExtractor to shift the x-axis to the mean
    def _move_to_mean(self):
        self.yt = _MethodsCollections._move_to_mean(self.yt)


    # Abstract method from featureExtractor to create the rFFT
    def _create_FFT(self):
        self.xf, self.yf = _MethodsCollections._create_FFT_C(self.yt)
        

    # Abstract method from featureExtractor to find the peaks
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
            raise Exception ("Fehler in der Methode _find_peaks_values() in Klasse Recoater. Fehlertyp: ", sys.exc_info()[0])




    ###Nur derzeitig zum Testen enthalten (kann später entfernt werden)
    def plot_test(self):
        """ Plot the diagramms of the time domain and freqency domain with the identified peaks to check the result """
        
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
            ax[1].set_ylabel('Spektrale Leistungsdichte')
            plt.ylim(-0.0000005, 0.000005) ###Achtung: Wurde angepasst

            # plot peaks
            ax[1].scatter(self.peaks_x, self.peaks_y, marker="x")

            fig.suptitle("Recoater")
            fig.tight_layout()
            plt.show ()
        
        except:
            raise Exception("Fehler in der Methode plot_test der Klasse Accousticplatform. Fehlertyp: ", sys.exc_info()[0])



    # Calculate the varianz
    def _var_time (y):
        return np.var(y)

    # Find peaks over a boundary in frequency domain 
    def _peaks_over_boundary_fre (yf):
        # TODO: Boundary Wert muss noch angepasst werden
        x = math.log10(2 * 1e-6)
        array = [math.log10(i) > x for i in yf]
        return sum(array)
    
    # Find peaks over a boundary in time domain 
    def _peaks_over_boundary_time (y):
        # TODO: Boundary Wert muss noch angepasst werden
        x = math.log10(0.2)
        array = [math.log10(i) > x for i in y]
        return sum(array)


    def get_feature(self):
        """ Determine the sensor specific features as array [variance, peaks over a boundary xxx in the frequency domain, peaks over a boundary xxx in the time domain]. 
            Call get_data and process before using this method otherwise this method throws a error.

        Returns:
            features (numpy.ndarray): Array with the sensor specific features. 
        """

        # zuvor: Vorverarbeitung der Sensordaten je Schicht über die Methoden get_data u. process und Herausschneiden der Spalte des Sensors "recoater"
        var = Recoater._var_time (self.yt)
        count_peaks_fre = Recoater._peaks_over_boundary_fre(self.yf)
        count_peaks_time = Recoater._peaks_over_boundary_time(self.yt)

        features = [var, count_peaks_fre, count_peaks_time]

        return features