"""
Subclass from Abstract Base Class featureExtractor that outputs features of the raw data that are required for machine learning models
"""

import numpy as np
import matplotlib.pyplot as plt
import h5py as h5
from scipy.signal import find_peaks
import sys
import math

from prosi3d.meta.featureExtractor import FeatureExtractor
from prosi3d.sensors.methodsCollection import MethodsCollections

class Accousticair(FeatureExtractor):

    def get_data(self, hdf):
        """ Abstract method from preprocessor to extract the data from the hdf5 """
       
        """ method to read teh hdf5 file """
        self._read_measurements(hdf)
        

    def process(self):
        """ Abstract method from preprocessor to process the data (FFT, find peaks) """
        
        """ method to replace nan values """
        self._replace_nan()
        
        """ method to shift the x-axis to the mean """
        self._move_to_mean()

        """ method to create the frequency datas (freqence, power spectral density) """
        self._create_FFT()

        """ method to find peaks """
        peaks = self._find_peaks_values()
        self.peaks_x = np.array([self.xf[peaks[0]]])
        self.peaks_y = np.array([self.yf[peaks[0]]])


    def write(self):
        """ Abstract method from preprocessor to print the peaks """
        ###Aktuell: Numpy array mit x-Werten von Peak und Numpy Array mit y-Werten von Peak
        print("x-Werte Peaks: ", self.peaks_x)
        print("y-Werte Peaks: ", self.peaks_y)


    def _read_measurements(self, hdf):
        """ Abstract method from freatureExtractor to create the time domain """
        sensorwert = 0 ###Sensorwert: Annahme 0!
        self.xt, self.yt = MethodsCollections._read_measurements_C(hdf, sensorwert)


    def _replace_nan(self): 
        """ Abstract method from featureExtractor to replace nan values with the mean of the neighboring values """
        self.yt = MethodsCollections._replace_nan_C(self.yt)
        

    def _move_to_mean(self):
        """ Abstract method from featureExtractor to shift the x-axis to the mean """
        self.yt = MethodsCollections._move_to_mean(self.yt)


    def _create_FFT(self):
        """ Abstract method from featureExtractor to create the rFFT """
        self.xf, self.yf = MethodsCollections._create_FFT_C(self.yt)
        

    def _find_peaks_values(self):
        """ Abstract method from featureExtractor to find the peaks """
        
        try:
            ###Parameter müssen noch gewählt werden, siehe https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html
            height = 1*1e-6
            distance = None
            prominence = None

            """return value: indices of the peaks"""
            peaks = find_peaks(self.yf, height, distance, prominence)
            
            return peaks
        except:
            raise Exception ("Fehler in der Methode _find_peaks_values() in Klasse Accousticair. Fehlertyp: ", sys.exc_info()[0])





    ###Nur derzeitig zum Testen enthalten (kann später entfernt werden)
    def plot_test(self):
        """ method to plot the diagramms and the peaks """
        try:
            fig, ax = plt.subplots(2)

            """ plot time Domain """
            ax[0].plot(self.xt, self.yt, linewidth=0.1)
            ax[0].set_title('Zeitbereich')
            ax[0].set_xlabel('Zeit in [ms]')
            ax[0].set_ylabel('Sensormesswert')

            """plot frequency domain"""
            ax[1].scatter(self.xf, self.yf, s=2)
            ax[1].set_title(f'Frequenzbereich')
            ax[1].set_xlabel('Frequenz in [Hz]')
            ax[1].set_ylabel('Spektale Leistungsdichte')
            plt.ylim(-0.0000005, 0.000005) ###Achtung: Wurde angepasst

            """plot peaks"""
            ax[1].scatter(self.peaks_x, self.peaks_y, marker="x")

            fig.suptitle("Accousticair")
            fig.tight_layout()
            plt.show ()
        
        except:
            raise Exception("Fehler in der Methode plot_test der Klasse Accousticair. Fehlertyp: ", sys.exc_info()[0])
    




    # Calculate the varianz 
    def _var_time (y):
        return np.var(y)

    # Find peaks over a boundary in frequency domain 
    def _peaks_over_boundary_fre (yf):
        # TODO: Boundary Wert muss noch angepasst werden
        x = 2 * 1e-6
        array = [math.log10(i) > x for i in yf]
        return sum(array)

    # Main component analyse 
    def _main_component_PCA (y):
        # TODO: Implementierung der Methode fehlt noch
        pass


    def get_feature(self):
        """ Determine the sensor specific features as array [variance, peaks over a boundary xxx in the frequency domain, main components of the PCA]. 
            Call get_data and process before using this method otherwise this method throws a error.

        Returns:
            features (numpy.ndarray): Array with the sensor specific features.
        """

        # zuvor: Vorverarbeitung der Sensordaten je Schicht über die Methoden get_data u. process und Herausschneiden der Spalte des Sensors "accousticair"
        var = Accousticair._var_time (self.yt)
        count_peaks_fre = Accousticair._peaks_over_boundary_fre(self.yf)
        count_main_component_PCA = Accousticair._main_component_PCA(self.yf)

        features = [var, count_peaks_fre, count_main_component_PCA]
            
        return features



