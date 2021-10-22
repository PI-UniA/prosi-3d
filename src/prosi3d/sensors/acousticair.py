"""
Subclass from Abstract Base Class featureExtractor that outputs features of the raw data that are required for machine learning models
"""

from os import lchown
import numpy as np
import matplotlib.pyplot as plt
import h5py as h5
from scipy.signal import find_peaks, argrelextrema
import sys
from scipy import signal

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
    

    def assignment_measurements_to_position(self, hdf_name):
        """
        Assign the sensor measurements to the EOS preprocessing data (x position, y position, partId, exposure) using the past time and the layer.

        Args:
            hdf (str): path of the hdf5 file.

        Returns:
            res_matrix (numpy.ndarray): Numy Array with (x, y, partId, exposure, measurement).

        Raises:
            AttributeError: No data available, call get_data() and process() before using the method assignment_measurements_to_position(hdf_name).

        """ 
        
        try: 

            # TTL Signal aus hdf herauslesen 
            # TODO: Macht es Sinn den Dateipfad als Attribute z.B. in Methode get_data zu hinterlegen (Parameter würde entfallen)? 
            hdf = h5.File(hdf_name, 'r')
            # Aus Rechenleistungsgründen wird nur der Anfang des TTL Signals betrachtet
            ttl = np.array(hdf.get('df')['block0_values'][:1000000, 1])

            # Glätten Bandpassfilter
            lowcut = 500.0
            highcut = 1250.0
            fs = 5000.0

            nyq = 0.5 * fs
            low = lowcut / nyq
            high = highcut / nyq

            order = 5
            Wn= [low, high]
            btype = 'bandpass'
            analog = False
            b, a = signal.butter(order, Wn, btype, analog)
            ttl_filtered = signal.filtfilt(b, a, ttl, axis=0)


            ### ungefiltertes Signal!!!

            # Ersten Peak (Maximum mit Wert > 1) suchen
            peaks_max = find_peaks (ttl, height = 1)[0]
            first_peak_x = peaks_max[0]
            first_peak_y = ttl[first_peak_x]

            # Lokales Minimum vor dem ersten Peak
            peaks_min = argrelextrema(ttl, np.less) [0]
            peaks_min = peaks_min[peaks_min <= first_peak_x]
            min_before_peak_x = peaks_min[-1]
            min_before_peak_y = ttl[min_before_peak_x]

            # Lokales Minimum oder Maximum vor dem ersten Peak, welches sich zwischen -0.05 und 0.05 befindet
            
            peaks_max = argrelextrema(ttl, np.greater) [0]
            peaks_max = peaks_max[peaks_max < first_peak_x]

            # Suche erstes lokales Maximum vor Peak innerhalb der Boundary
            i = -1
            while True:
                measurement = ttl[peaks_max[i]]
                if (measurement > -0.05) & (measurement < 0.05):
                    max_before_peak_x = peaks_max[i]
                    max_before_peak_y = measurement
                    break
                
                i = i - 1

            # Suche erstes lokales Minimum vor Peak innerhalb der Boundary
            i = -1
            while True:
                measurement = ttl[peaks_min[i]]
                if (measurement > -0.05) & (measurement < 0.05):
                    min_before_peak_mod_x = peaks_min[i]
                    min_before_peak_mod_y = measurement
                    break
                
                i = i - 1
            
            if min_before_peak_mod_x > max_before_peak_x:
                point_mod_x = min_before_peak_mod_x
                point_mod_y = min_before_peak_mod_y
            else:
                point_mod_x = max_before_peak_x
                point_mod_y = max_before_peak_y

            
            ### gefiltertes Signal!!

            # Ersten Peak (Maximum mit Wert > 1) suchen
            peaks_max_filtered = find_peaks (ttl_filtered, height = 1)[0]
            first_peak_x_filtered = peaks_max_filtered[0]
            first_peak_y_filtered = ttl_filtered[first_peak_x_filtered]

            # Lokales Minimum vor dem ersten Peak
            peaks_min_filtered = argrelextrema(ttl_filtered, np.less) [0]
            peaks_min_filtered = peaks_min_filtered[peaks_min_filtered <= first_peak_x_filtered]
            min_before_peak_x_filtered = peaks_min_filtered[-1]
            min_before_peak_y_filtered = ttl_filtered[min_before_peak_x_filtered]

            # Lokales Minimum oder Maximum vor dem ersten Peak, welches sich zwischen -0.05 und 0.05 befindet
            peaks_max = argrelextrema(ttl_filtered, np.greater) [0]
            peaks_max = peaks_max[peaks_max < first_peak_x_filtered]
            
            # Suche erstes lokales Maximum vor Peak innerhalb der Boundary
            i = -1
            while True:
                measurement_filtered = ttl_filtered[peaks_max[i]]
                if (measurement_filtered > -0.05) & (measurement_filtered < 0.05):
                    max_before_peak_x_filtered = peaks_max[i]
                    max_before_peak_y_filtered = measurement_filtered
                    break
                
                i = i - 1



            # Suche erstes lokales Minimum vor Peak innerhalb der Boundary
            i = -1
            while True:
                measurement_filtered = ttl_filtered[peaks_min_filtered[i]]
                if (measurement_filtered > -0.05) & (measurement_filtered < 0.05):
                    min_before_peak_mod_x_filtered = peaks_min_filtered[i]
                    min_before_peak_mod_y_filtered = measurement_filtered
                    break
                
                i = i - 1
            
            if min_before_peak_mod_x_filtered > max_before_peak_x_filtered:
                point_mod_x_filtered = min_before_peak_mod_x_filtered
                point_mod_y_filtered = min_before_peak_mod_y_filtered
            else:
                point_mod_x_filtered = max_before_peak_x_filtered
                point_mod_y_filtered = max_before_peak_y_filtered



            # Bereich mit ersten Peak noch nicht errreicht, ganzes TTL Signal wird betrachtet
            # if (peaks_max.size == 0):

            #     # Ersten Peak (Maximum mit Wert > 1) suchen
            #     peaks_max = find_peaks (ttl, height = 1)[0]
            #     first_peak_x = peaks_max[0]
            #     first_peak_y = ttl[first_peak_x]

            #     # Lokales Minimum vor dem ersten Peak
            #     peaks_min = argrelextrema(ttl, np.less) [0]
            #     peaks_min = peaks_min[peaks_min <= first_peak_x]
            #     min_before_peak_x = peaks_min[-1]
            #     min_before_peak_y = ttl[min_before_peak_x]

            #     # Lokales Minimum vor dem ersten Peak, welches sich zwischen -0.01 und 0.01 befindet
            #     i = -1
            #     while True:
            #         measurement = ttl[peaks_min[i]]
            #         if (measurement > -0.01) & (measurement < 0.01):
            #             min_before_peak_mod_x = peaks_min[i]
            #             min_before_peak_mod_y = measurement
            #             break
                    
            #         i = i - 1
            

            #unfilterd
            print("First Peak :", "(", first_peak_x, ",", first_peak_y, ")")
            print("Min before peak:" , "(", min_before_peak_x, ", ", min_before_peak_y, ")")
            print("Min before peak (modified):" , "(", point_mod_x, ", ", point_mod_y, ")")

            #filtered
            print("First Peak (filtered) :", "(", first_peak_x_filtered, ",", first_peak_y_filtered, ")")
            print("Min before peak (filtered):" , "(", min_before_peak_x_filtered, ", ", min_before_peak_y_filtered, ")")
            print("Min before peak (modified, filtered):" , "(", point_mod_x_filtered, ", ", point_mod_y_filtered, ")")
            
            #filtered and unfiltered in one graph
            plt.plot(np.arange(470000,480000,1), ttl[470000:480000], linewidth=0.1,  c='r', label = "unfiltered")
            plt.plot(min_before_peak_x, min_before_peak_y, marker ='x', c='r')
            plt.plot(point_mod_x, point_mod_y, marker ='x', c='r')
            plt.plot(first_peak_x, first_peak_y,  marker = 'x', c='r')

            plt.plot(np.arange(470000,480000,1), ttl_filtered[470000:480000], linewidth=0.1,  c='b', label = "filtered")
            plt.plot(min_before_peak_x_filtered, min_before_peak_y_filtered, marker ='x', c='b')
            plt.plot(point_mod_x_filtered, point_mod_y_filtered, marker ='x',  c='b')
            plt.plot(first_peak_x_filtered, first_peak_y_filtered,  marker = 'x',  c='b')

            plt.legend()
            plt.show()


            #only unfiltered 
            plt.plot(np.arange(470000,480000,1), ttl_filtered[470000:480000], linewidth=0.1,  c='b',label = "filtered")
            plt.plot(min_before_peak_x_filtered, min_before_peak_y_filtered, marker ='x', c='b')
            plt.plot(point_mod_x_filtered, point_mod_y_filtered, marker ='x',  c='b')
            plt.plot(first_peak_x_filtered, first_peak_y_filtered,  marker = 'x',  c='b')

            plt.legend()
            plt.show()




            # konstante Zeit zwischen zwei Sensorwerten: 50 kHz 
            time_between_measurements = 1/50000 # TODO: Wert richtig?
            
            # Start
            start_value = 47330 # TODO: x-Wert von oben zuweisen
            time = 0

            #Beispiel-Array zum Testen: 
            example = np.array([[5,5,1,7], [5,10,1,7], [5,15,2,7]])
            i=0

            # Startwerte setzen: time = 0 
            #res_matrix = np.append(getXY_lin(0, layer), ttl[start_value]
            res_matrix = np.append(example[0], ttl[start_value])
            # 1D to 2D Array
            res_matrix = np.reshape(res_matrix,(1, res_matrix.size))

            #for value in range (start_value+1, ttl.shape[0]+1):
            for value in range (start_value+1, start_value + example.shape[0]):
                    
                # mit Björns Methode: getXY_lin --> Input: Zeit, Layer --> Output: Array (xtime, ytime, int (partId), int (exposure))
                # TODO: layer bestimmen (aus hdf_name oder als Parameter an Methode übergeben?)
                time = time + time_between_measurements
                #laser_values = getXY_lin(time, layer)
                
                #zum Testen
                i=i+1
                laser_values = example[i]

                # Dazugehörigen Sensorwert bestimmen
                measurement = self.yt [value]

                #Zusammenfügen für bestimmten Zeitwert time
                new = np.append(laser_values, measurement)
                
                #Ans Array hinzufügen (je Zeitwert eine Zeile)
                res_matrix = np.append(res_matrix,[new],axis= 0)

            print ("MATRIX", res_matrix)

            return res_matrix


        except AttributeError:
            raise Exception("Call get_data() and process() before using the method assignment_measurements_to_position(hdf_name).")

        except:
            raise Exception("Fehler in der Methode assignment_measurements_to_position der Klasse Accousticair. Fehlertyp: ", sys.exc_info()[0])
    


        
        



