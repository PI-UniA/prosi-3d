""" Subclass from Abstract Base Class featureExtractor that outputs features of the raw data that are required for machine learning models """

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from tqdm import tqdm
import h5py as h5
from scipy.signal import find_peaks
import sys
import math

from prosi3d.meta.featureExtractor import FeatureExtractor
from prosi3d.sensors._methodsCollection import _MethodsCollections
from prosi3d.preprocessing.preprocessing import filesInFolder_simple

def lab2hdf_4ch_simple(path):
    '''
    Process 4-channel layerwise acoustic measurement txt files written by labview and saves as hdf-files with pandas dataframe key='df'.
    Timestamp is changed to float total seconds starting with zero in each layer.
    If day changes, then 24*60*60 seconds are added to each float value of the new day.
    By this, the maximum processable layertime is 24 hours.
    Calls folder2Files to get ttldir in project path and collects all txt files by calling filesInfolder() from ttldir.
    
    Args: path
    Returns: <saved h5 files>
    '''
    
    #files = [f.path for f in os.scandir(ttldir)]
    files = filesInFolder_simple(path, typ='txt')

    #print('1,3 Gbyte equal around 10 Mio lines.')
    # iterate all files by line in fopen object is less memory-expensive then read_csv. files can have billions of rows.
    n = 1
    for fname in tqdm(files):
        f = open(fname, "r", encoding='UTF-8')
        df = []
        for line in f:
            # if length equals two indexError occurs
            # valid rows have ':' at third place (timestamp)
            if len(line) > 2 and line[2] == ':':
                if line[2] == ':':
                    # linebreaks
                    line = line.replace('\n','')
                    # decimal symbol
                    line = line.replace(',','.')
                    # column delimiter
                    val = line.split('\t')
                    # float voltage values
                    val[1:] = list(map(float, val[1:]))
                    df.append(val)
        f.close()
        #logger.info('List complete. Changing to DataFrame ...')
        df = pd.DataFrame(df)
        df.columns = ['time', 'lse', 'ttl', 'kse_bp', 'kse_rec']
        #logger.info('DataFrame done. Changing string to timedelta ...')

        #df['time'] = pd.to_datetime(df['time'])
        df['time'] = pd.to_timedelta(df['time'])
        #logger.info('Timedelta done. Changing to total seconds ...')
        # start time with zero in every layer and convert by this to seconds
        df['time'] = df['time'] - df['time'].iloc[0]
        df['time'] = df['time'].dt.total_seconds()
        #logger.info(df.iloc[:,0].dtype)
        
        #df.iloc[:,0] = df.iloc[:,0].values.astype('datetime64[ns]')
        #df.iloc[:,0] = df.iloc[:,0].map(lambda x: x.total_seconds())
        
        #logger.info('Formatting done. Write hdf5 ...')
        
        # if daychange within one layer then add 24 hours
        tmin = df['time'].min()
        tmax = df['time'].max()
        dayboarder = df.loc[df['time'] == tmin].index[0]
        if dayboarder > df.loc[df['time'] == tmax].index[0]:
            
            df.loc[dayboarder:, 'time'] = df.loc[dayboarder:, 'time'].copy() + 24*60*60
            
        # Saving files
        a = fname.rfind('_lay')
        b = fname.rfind('.')
        layer = fname[a+4:b]
        name = path + '\\' + 'ch4raw_' + str(layer).zfill(5) + '.h5'
        df.to_hdf(name, key='df', mode='w')
        out = 'Layer: ' + layer + ' saved as hdf5.'
        #logger.info(out)
        n+=1

class Accousticplatform(FeatureExtractor):

    """ 
    Attribute: 
        peaks_x (numpy.ndarray): frequency of the peaks.
        
        peaks_y (numpy.ndarray): spectral power density of the peaks.
    """


    
    def get_data(self, hdf):
        """ Extract the measurements of the accousticplatform sensor from the hdf5 file.
        
        Args:
            hdf (str): path of the hdf5 file.

        Raises:
            IOError: File can not found.
        """
       
        # method to read the hdf5 file
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
        """
        Print the x-values and the y-values of the peaks which are saved in to numpy arrays.
        """
        print("x-Werte Peaks: ", self.peaks_x)
        print("y-Werte Peaks: ", self.peaks_y)


    # Abstract method from freatureExtractor to create the time domain
    def _read_measurements(self, hdf):
        
        # Measurements of the accousticplatform in column 3
        sensorwert = 2 
        self.xt, self.yt = _MethodsCollections._read_measurements_C(hdf, sensorwert)


    # Abstract method from featureExtractor to replace nan values with the mean of the neighboring values
    def _replace_nan(self): 
        self.yt = _MethodsCollections._replace_nan_C(self.yt)
        

    # Abstract method from featureExtractor to shift the x-axis to the mean
    def _move_to_mean(self):
        self.yt = _MethodsCollections._move_to_mean(self.yt)


    # Abstract method from featureExtractor to create the rFFT """
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
            raise Exception ("Fehler in der Methode _find_peaks_values() in Klasse Accousticplatform. Fehlertyp: ", sys.exc_info()[0])





    # Nur derzeitig zum Testen enthalten (kann später entfernt werden)
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

            fig.suptitle("Accousticplatform")
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

        # zuvor: Vorverarbeitung der Sensordaten je Schicht über die Methoden get_data u. process und Herausschneiden der Spalte des Sensors "accousticplatform"
        var = Accousticplatform._var_time (self.yt)
        count_peaks_fre = Accousticplatform._peaks_over_boundary_fre(self.yf)
        count_peaks_time = Accousticplatform._main_component_PCA(self.yf)

        features = [var, count_peaks_fre, count_peaks_time]
        
        return features
