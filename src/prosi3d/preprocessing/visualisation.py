import matplotlib
import matplotlib.pyplot as plt
import os
import pandas as pd

def vectors_view(lay,path=0,pdf=1,color_vector=0,jumps=0,solved_vectors=False):
    '''
    generates graphical representation of eosprint makro scan vectors either via qt5 or saved as pdf (pdf=1 saves pdf instead of qt5 inline plot)
    jumps = 1 swaps order to show jumps
    color_vector = >123< colors vector number 123
    calls function setcolor()
    give it a layer number and project path or give it a filepath
    
    Args: lay,path=0,pdf=1,color_vector=0,jumps=0,solved_vectors=False
    Returns: <none>
    '''
    
    # save pdf or plot qt5 chart
    if pdf == 0:
        matplotlib.use('Qt5Agg')
    else:
        matplotlib.use('pdf')
    
    # check if file or layer number is given
    try:
        # if invalid literal for int --> except: assume direct filepath was intered
        num = int(lay)
        if lay == num:
            if path == 0:
                print('Layer number entered but no project directory/path')
            else:
                # either use raw eosprint_layer or solved eosprint_corr_layer file
                _, _, _, vecdir, _, _, _, _ = folder2Files(path,0)
                if solved_vectors==True:
                    f = vecdir + '\\' + "eosprint_corr_layer" + str(lay).zfill(5) + ".h5"
                else:
                    f = vecdir + '\\' + "eosprint_layer" + str(lay).zfill(5) + ".h5"
    except:
        # true if it is a file -> then it should be the direct file for processing
        if os.path.isfile(lay):
            f = lay
    
    # read file and reset index
    df = pd.read_hdf(f, 'df')
    df.reset_index(drop=True, inplace=True)
    
    # size definition for plotting in inches
    plt.figure(figsize=(96,96))
    ax = plt.axes()
    ax.set_aspect('equal')
    # build plattform size
    plt.xlim(0, 250)
    plt.ylim(0, 250)
    
    ## first layer has odd line number count in previous versions of eosprintsdk
    # odd line numbers: skip first line (index 0) and use then following pairs
    if solved_vectors==False:
        if len(df)%2 == 1:
            a = 1
            if jumps==1:
                a = 0
        # even line numbers: use following pairs starting with first line 
        else:
            a = 0
            if jumps==1:
                a = 1
    else:
        a = 0
    
    ## TODO *2 +1 only if jumps are to be plotted does not make sense
    if jumps == 1 and color_vector != 0:
        color_vector = color_vector*2+1
    
    # iterate rows, set color depending on exposuretype and draw vector arrows
    # eosprint_layer file
    if solved_vectors==False:
        for i, row in df.iterrows():
            if (i%2 == a):
                # set color for vector which should be marked
                if color_vector != 0 and color_vector == i:
                    col = 'crimson'
                else:
                    col = setcolor(df.iloc[i,2])
                j = i + 1
                vec = [df.iloc[i,0], df.iloc[i,1], df.iloc[j,0]-df.iloc[i,0], df.iloc[j,1]-df.iloc[i,1]]
                ax.arrow(*vec, head_width=0.05, head_length=0.1, color=col)
            # abort before index error
            if i + 1 == len(df) -1:
                break
        
    # eosprint_corr_layer file
    else:
        for i, row in df.iterrows():
            # set vector color
            col = setcolor(df.iloc[i,7])
            # x0, y0, x1-x0, y1-y0
            vec = [df.iloc[i,0], df.iloc[i,1], df.iloc[i,2]-df.iloc[i,0], df.iloc[i,3]-df.iloc[i,1]]
            ax.arrow(*vec, head_width=0.05, head_length=0.1, color=col)

    #print('Count of vectorpairs:')
    #print(df.groupby('exposureType').count())
    #plt.show()
    #time.sleep(180)

    # save file as pdf, clear memory and reset qt5 as standard graphic engine
    if pdf == 1:
        # without file ending
        fname = f.rsplit('.',1)[0]
        # other folder
        fname = fname.replace('\\vec\\', '\\pdf\\')
        plt.savefig(fname + '.pdf', format='pdf', dpi=600)
        #plt.savefig(f[0:19] + '_2.svg', format='svg')
        #plt.savefig(f[0:19] + '.png', dpi=50)
        plt.close()
        del(df)
        matplotlib.use('Qt5Agg')