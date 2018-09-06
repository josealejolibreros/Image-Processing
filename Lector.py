import dicom
import numpy as np #is a standard to use this alias for NumPy package
import os

from matplotlib import pyplot as plt


class Lector(object):
    '''
    PathDicom = "." 
    lstFilesDCM = []  # create an empty list
    for dirName, subdirList, fileList in os.walk(PathDicom):
        for filename in fileList:
            if ".dcm" in filename.lower():  # check whether the file's DICOM
                lstFilesDCM.append(os.path.join(dirName,filename))
            
    #Lets check what we have in the list
    print(lstFilesDCM)


    # Get ref file
    RefDs = dicom.read_file(lstFilesDCM[0])

    # Load dimensions based on the number of rows, columns, and slices (along the Z axis)
    ConstPixelDims = (int(RefDs.Rows), int(RefDs.Columns), len(lstFilesDCM))

    # Load spacing values (in mm)
    try:
        SliceThickness = float(RefDs.SliceThickness)
    except AttributeError:
        SliceThickness = 1.0

    ConstPixelSpacing = (float(RefDs.PixelSpacing[0]), float(RefDs.PixelSpacing[1]), SliceThickness)


    print(RefDs)
    print(ConstPixelDims)
    print(ConstPixelSpacing)

    #Create the array staring from 0, to ConstPixelDims[0]+1 (because stop is an open interval) 
    #and the ConstPixelSpacing gives the scale to the volume. 
    #If ConstPixelSpacing == 1, then values go to ConstPixelDims[0]+1. It creates a cube.

    x = np.arange(0.0, (ConstPixelDims[0]+1)*ConstPixelSpacing[0], ConstPixelSpacing[0])
    y = np.arange(0.0, (ConstPixelDims[1]+1)*ConstPixelSpacing[1], ConstPixelSpacing[1])
    z = np.arange(0.0, (ConstPixelDims[2]+1)*ConstPixelSpacing[2], ConstPixelSpacing[2])

    half = int(np.round(x.shape[0] / 2))
    print(x[:half]) #print half the values. Starting from index 0 to half-1


    # The array is sized based on 'ConstPixelDims'
    ArrayDicom = np.zeros(ConstPixelDims, dtype=RefDs.pixel_array.dtype)

    # loop through all the DICOM files
    for filenameDCM in lstFilesDCM:
        # read the file
        ds = dicom.read_file(filenameDCM)
        # store the raw image data
        ArrayDicom[:, :, lstFilesDCM.index(filenameDCM)] = ds.pixel_array


    plt.figure(dpi=300)
    plt.axes().set_aspect('equal')
    plt.set_cmap(plt.gray())

    #If you are using MAMMOGRAPHY_PRESENTATION.dcm or MAMMOGRAPHY_RAW.dcm use
    plt.pcolormesh(x, y, np.flipud(ArrayDicom[:, :, 0]).T)
    #else, use the line below
    #plt.pcolormesh(x, y, np.flipud(ArrayDicom[:, :, 0]))

    plt.imshow(np.flipud(ArrayDicom[:, :, 0]))
    '''
    pass




