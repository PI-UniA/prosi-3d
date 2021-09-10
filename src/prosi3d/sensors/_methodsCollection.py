import numpy as np
import h5py as h5
import sys
from scipy.fft import rfft, fftfreq

class _MethodsCollections():

    """
    MethodsCollections contains a collection of methods which are the same for all sensors. All methods are private and called in the specific methods of the sensors.
    """
      
    def _read_measurements_C(hdf_name, sensorwert):
        """ method for all sensors to read the hdf5 file
        """
        try:
            # parameter sensorwert contains the specific column of the measurements
            
            hdf = h5.File(hdf_name, 'r')

            # Extract Measurements for the y-axis
            measurements = np.array(hdf.get('df')['block0_values'][0:10000, sensorwert]) # TODO (anna-lena): Achtung: nicht alle Werte, um besser testen zu können!
            global sample_number 
            sample_number = measurements.shape[0]
            
            time_total = ((90/61844730) * 10000) * 60 * 1000 # TODO (anna-lena): darf nicht fix bleiben! (Annahme: ((Gesamtzeit/Gesamtanzahl Samples) * Anzahl betrachteter Werte) * 60 [s] * 1000 [ms]
            time_step = time_total / sample_number #in Millisekunden

            # Extract time scale for the x-axis
            time = np.arange (0, time_total, time_step)

            return time, measurements
        

        except IOError:
            raise Exception("The file can not be found!")

        except:
            raise Exception("Fehler in der Methode _read_measurements_C der Klasse MethodsCollection. Fehlerklasse: ", sys.exc_info()[0])



    def _replace_nan_C(series): 

        """ method for all sensors to replace the nan values with the mean of the neighboring values
        """
        try:

            # Identify the index of nan values """ 
            nan_yt = np.argwhere(np.isnan(series))

            for i in range(0, nan_yt.size):
                index = nan_yt[i][0]
                
                # continue if the previous value was nan, too
                if (index - 1 == nan_yt[i - 1]):
                    continue
                
                # multiple nan values side by side 
                if ((i < nan_yt.size - 1) and (nan_yt[i + 1] == index + 1)):
                    
                    j = 1
                    # count the nan values 
                    while (nan_yt[i + j] == index + j):
                        j = j + 1
                    
                    mean = (series[index - 1] + series [index + j]) / 2
                    # Replace the nan values with the mean 
                    for x in range(index, index + j):
                        series[x] = mean

                
                else:
                    # normal case: next to the nan value are decimal numbers
                    if index == 0:
                        # First value: replace with the next value
                        series[index] = series[index + 1]
                    elif index == series.size - 1:
                        # Last value: replace with the penultimate value
                        series[index]= series[index - 1]
                    else:
                        # Replace with the mean of the two neighboring values
                        series[index] = (series[index - 1] + series[index + 1]) / 2
                      
            
            return series

        except:
            raise Exception("Fehler in der Methode _replace_nan_C in der Klasse MethodsCollection. Fehlertyp: ", sys.exc_info()[0])


    def _move_to_mean(series):
        
        """ method for all sensors to shift the x-axis to the mean
        """
        
        data_mean = np.mean(series)
        series = series - data_mean
        return series


    def _create_FFT_C(y):
        """ method for all sensors to create the rFFT
        """
        
        # Source: https://docs.scipy.org/doc/scipy/reference/tutorial/fft.html 
        try:
            # N: amount of samples; T: timestep 
            N = len(y) 
            T = ((90 * 60) / 61844730) # TODO (anna-lena): Anpassung notwendig (Gesamtzeit * 60 [für s --> Hz] / Gesamtanzahl)

            # Fourier transformation y-values: complex values, one-sided, calculate the Power-Spectral-Density
            yf = rfft(y)
            yf = 2.0/N * np.abs(yf[0:N//2])
            yf = np.power(yf, 2)
            
            # Fourier transformation x-values: cut off the second half, one-sided
            xf = fftfreq(N, T)[:N//2] 
            
            return xf, yf

        except:
            raise Exception("Fehler in der Methode _create_FFT_C in der Klasse MethodsCollection. Fehlertyp: ", sys.exc_info()[0])


    