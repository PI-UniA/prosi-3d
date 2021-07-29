from prosi3d.meta.featureExtractor import FeatureExtractor
import numpy as np
import matplotlib.pyplot as plt

from scipy.fft import fft, fftfreq
from scipy.signal import find_peaks

""" Subclass from Abstract Base Class featureExtractor that outputs features of the raw data that are required for machine learning models """
class Accousticair(FeatureExtractor):

    """
    xxxxx
    """


    def __init__(self):
        # self.xt = None
        # self.yt = None
        # self.xf = None
        # self.yf = None
        # self.peaks_x = None
        # self.peaks_y = None
        pass


    """ Abstract method from preprocessor to extract the data from the hdf5 """
    def get_data(self, hdf):

        ###hdf zuvor überprüfen?
        xt, yt = self._read_measurements(hdf)
        ###Überprüfung auf Fehler
        self.xt = xt
        self.yt = yt


    """ Abstract method from preprocessor to process the data (FFT, find peaks) """
    def process(self):

        """ Call the method to replace nan values """
        self._replace_nan()
        
        """ Shifting so that the x-axis is equals to the mean """
        data_mean = np.mean(self.yt)
        self.yt = self.yt - data_mean

        """ Call the method to create the frequency datas (freqence, power spectral density) """
        frequence, psd = self._create_FFT()
        self.xf = frequence
        self.yf = psd

        """ Call the method to find peaks """
        peaks = self._find_peaks_values()
        self.peaks_x = np.array([self.xf[peaks[0]]])
        self.peaks_y = np.array([self.yf[peaks[0]]])


    """ Abstract method from preprocessor to print the peaks """
    def write(self):
        ###Aktuell: Numpy array mit x-Werten von Peak und Numpy Array mit y-Werten von Peak
        print("x-Werte Peaks: ", self.peaks_x)
        print("y-Werte Peaks: ", self.peaks_y)


    """ Abstract method from freatureExtractor to create the time domain """
    def _read_measurements(self, hdf):
        
        ###Abfragen, ob in welcher Spalte accousticair Werte stehen
        ###aktuelle Annahme: Immer gleiche Spalte
        sensorwert = 0

        """ Extract Measurements for the y-axis """
        measurements = np.array(hdf.get('df')['block0_values'][0:10000, sensorwert]) ##Achtung: nicht alle Werte, um besser testen zu können!
        sample_number = measurements.shape[0]
        
        self.time_total = ((90/61844730) * 10000) * 60 * 1000 ###darf nicht fix bleiben! (Annahme: ((Gesamtzeit/Gesamtanzahl Samples) * Anzahl betrachteter Werte) * 60 [s] * 1000 [ms]

        time_step = self.time_total / sample_number #in Millisekunden

        """ Extract time scale for the x-axis """
        time = np.arange (0, self.time_total, time_step)

        return time, measurements


    """ Abstract method from featureExtractor to replace nan values with the mean of the neighboring values """
    def _replace_nan(self): 
        """ Identify the index of nan values """ 
        nan_yt = np.argwhere(np.isnan(self.yt))

        for i in range(0, nan_yt.size):
            index = nan_yt[i]

            if index == 0:
                """ First value: replace with the next value """
                self.yt[index] = self.yt[index+1]
            elif index == self.yt.size - 1:
                """ Last value: replace with the penultimate value """
                self.yt[index]= self.yt[index-1]
            else:
                """ Replace with the mean of the two neighboring values """
                self.yt[index] = (self.yt[index-1] + self.yt[index+1])/2


    """ Abstract method from featureExtractor to create the FFT """
    def _create_FFT(self):
        """ Source: https://docs.scipy.org/doc/scipy/reference/tutorial/fft.html """
    
        """ N: amount of samples; T: timestep """
        N = len(self.yt) 
        T = ((90 * 60) / 61844730) ###Anpassung notwendig (Gesamtzeit * 60 [für s --> Hz] / Gesamtanzahl)

        """Fourier transformation y-values: complex values"""
        yf = fft(self.yt)
        #Einseitig und Berechnung der spektralen Leistungsdichte
        yf = 2.0/N * np.abs(yf[0:N//2])
        yf = np.power(yf, 2)
        
        """Fourier transformation x-values"""
        #Fourier transformiert --> frequenz (Abschneiden 2. Hälfte, da negativ --> einseitg)
        xf = fftfreq(N, T)[:N//2] 
        
        return xf, yf


    """ Abstract method from featureExtractor to find the peaks """
    def _find_peaks_values(self):
        ###Parameter müssen noch gewählt werden, siehe https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html
        height = 1*1e-6
        distance = None
        prominence = None

        #return value: index of the peaks
        peaks = find_peaks(self.yf, height, distance, prominence)
        
        return peaks


    """ Method to plot the diagramms and the peaks """
    ###Nur derzeitig zum Testen enthalten (kann später entfernt werden)
    def plot_test(self):
        fig, ax = plt.subplots(2)
        #plot time Domain
        ax[0].plot(self.xt, self.yt, linewidth=0.1)
        ax[0].set_title('Zeitbereich')
        ax[0].set_xlabel('Zeit in [ms]')
        ax[0].set_ylabel('Sensormesswert')

       #plot frequency domain
        ax[1].scatter(self.xf, self.yf, s=2)
        ax[1].set_title(f'Frequenzbereich')
        ax[1].set_xlabel('Frequenz in [Hz]')
        ax[1].set_ylabel('Spektale Leistungsdichte')
        plt.ylim(-0.0000005, 0.000005)

        #plot peaks
        ax[1].scatter(self.peaks_x, self.peaks_y, marker="x")

        fig.tight_layout()
        plt.show ()
    






