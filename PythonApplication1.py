# pydicom_Tkinter.py
#
# Copyright (c) 2009 Daniel Nanz
# This file is released under the pydicom
# (https://github.com/pydicom/pydicom)
# license, see the file LICENSE available at
# (https://github.com/pydicom/pydicom)
#
# revision history:
# Dec-08-2009: version 0.1
#
# 0.1:   tested with pydicom version 0.9.3, Python version 2.6.2 (32-bit)
#        under Windows XP Professional 2002, and Mac OS X 10.5.5,
#        using numpy 1.3.0 and a small random selection of MRI and
#        CT images.
'''
View DICOM images from pydicom
requires numpy:  http://numpy.scipy.org/
Usage:
------
import pydicom              # pydicom
import pydicom.contrib.pydicom_Tkinter as pydicom_Tkinter    # this module
df = pydicom.read_file(filename)
pydicom_Tkinter.show_image(df)
'''
import pydicom              # pydicom
import tempfile
import os
import matplotlib
matplotlib.use("TKAgg")

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import dicom
from pydicom.compat import in_py2

from skimage import exposure
if in_py2:
    import Tkinter as tkinter

have_numpy = True
try:
    import numpy as np
except ImportError:
    # will not work...
    have_numpy = False


from PIL import Image

from resizeimage import resizeimage

def get_PGM_bytedata_string(arr):
    '''Given a 2D numpy array as input write
    gray-value image data in the PGM
    format into a byte string and return it.
    arr: single-byte unsigned int numpy array
    note: Tkinter's PhotoImage object seems to
    accept only single-byte data
    '''

    if arr.dtype != np.uint8:
        raise ValueError
    if len(arr.shape) != 2:
        raise ValueError

    # array.shape is (#rows, #cols) tuple; PGM input needs this reversed
    col_row_string = ' '.join(reversed([str(x) for x in arr.shape]))

    bytedata_string = '\n'.join(('P5', col_row_string, str(arr.max()),
                                 arr.tostring()))
    return bytedata_string


def get_PGM_from_numpy_arr(arr,
                           window_center,
                           window_width,
                           lut_min=0,
                           lut_max=255):
    '''real-valued numpy input  ->  PGM-image formatted byte string
    arr: real-valued numpy array to display as grayscale image
    window_center, window_width: to define max/min values to be mapped to the
                                 lookup-table range. WC/WW scaling is done
                                 according to DICOM-3 specifications.
    lut_min, lut_max: min/max values of (PGM-) grayscale table: do not change
    '''

    if np.isreal(arr).sum() != arr.size:
        raise ValueError

    # currently only support 8-bit colors
    if lut_max != 255:
        raise ValueError

    if arr.dtype != np.float64:
        arr = arr.astype(np.float64)

    # LUT-specific array scaling
    # width >= 1 (DICOM standard)
    window_width = max(1, window_width)

    wc, ww = np.float64(window_center), np.float64(window_width)
    lut_range = np.float64(lut_max) - lut_min

    minval = wc - 0.5 - (ww - 1.0) / 2.0
    maxval = wc - 0.5 + (ww - 1.0) / 2.0

    min_mask = (minval >= arr)
    to_scale = (arr > minval) & (arr < maxval)
    max_mask = (arr >= maxval)

    if min_mask.any():
        arr[min_mask] = lut_min
    if to_scale.any():
        arr[to_scale] = ((arr[to_scale] - (wc - 0.5)) /
                         (ww - 1.0) + 0.5) * lut_range + lut_min
    if max_mask.any():
        arr[max_mask] = lut_max

    # round to next integer values and convert to unsigned int
    arr = np.rint(arr).astype(np.uint8)

    # return PGM byte-data string
    return get_PGM_bytedata_string(arr)


def get_tkinter_photoimage_from_pydicom_image(data):
    '''
    Wrap data.pixel_array in a Tkinter PhotoImage instance,
    after conversion into a PGM grayscale image.
    This will fail if the "numpy" module is not
    installed in the attempt of creating the data.pixel_array.
    data:  object returned from pydicom.read_file()
    side effect: may leave a temporary .pgm file on disk
    '''

    # get numpy array as representation of image data
    arr = data.pixel_array.astype(np.float64)

    # pixel_array seems to be the original, non-rescaled array.
    # If present, window center and width refer to rescaled array
    # -> do rescaling if possible.
    if ('RescaleIntercept' in data) and ('RescaleSlope' in data):
        intercept = data.RescaleIntercept  # single value
        slope = data.RescaleSlope
        arr = slope * arr + intercept

    # get default window_center and window_width values
    wc = (arr.max() + arr.min()) / 2.0
    ww = arr.max() - arr.min() + 1.0

    # overwrite with specific values from data, if available
    if ('WindowCenter' in data) and ('WindowWidth' in data):
        wc = data.WindowCenter
        ww = data.WindowWidth
        try:
            wc = wc[0]  # can be multiple values
        except Exception:
            pass
        try:
            ww = ww[0]
        except Exception:
            pass

    # scale array to account for center, width and PGM grayscale range,
    # and wrap into PGM formatted ((byte-) string
    pgm = get_PGM_from_numpy_arr(arr, wc, ww)

    # create a PhotoImage
    # for as yet unidentified reasons the following fails for certain
    # window center/width values:
    #         photo_image = Tkinter.PhotoImage(data=pgm, gamma=1.0)
    #    Error with Python 2.6.2 under Windows XP:
    #          (self.tk.call(('image', 'create', imgtype, name,) + options)
    #          _tkinter.TclError: truncated PPM data
    #    OsX: distorted images
    # while all seems perfectly OK for other values of center/width or when
    # the PGM is first written to a temporary file and read again

    # write PGM file into temp dir
    (os_id, abs_path) = tempfile.mkstemp(suffix='.pgm')
    with open(abs_path, 'wb') as fd:
        fd.write(pgm)

    

    from PIL import ImageTk as itk
    background = "background.png"
    imagenoreb = Image.open(abs_path)
    width = 500
    height = 500
    im2 = imagenoreb.resize((width,height))
    im2 = itk.PhotoImage(im2)
    
    photo_image = im2
    '''
    photo_image = tkinter.PhotoImage(file=abs_path, gamma=1.0)
    photo_image = tkinter.PhotoImage(im2)
    '''
    
    

    # close and remove temporary file on disk
    # os.close is needed under windows for os.remove not to fail
    try:
        os.close(os_id)
        os.remove(abs_path)
    except Exception:
        pass  # silently leave file on disk in temp-like directory

    return photo_image


def show_image(data, block=True, master=None):
    '''
    Get minimal Tkinter GUI and display a pydicom data.pixel_array
    data: object returned from pydicom.read_file()
    block: if True run Tk mainloop() to show the image
    master: use with block==False and an existing
    Tk widget as parent widget
    side effects: may leave a temporary .pgm file on disk
    '''
    frame = tkinter.Frame(master=master, background='#000')
    if 'SeriesDescription' in data and 'InstanceNumber' in data:
        title = ', '.join(('Ser: ' + data.SeriesDescription,
                           'Img: ' + str(data.InstanceNumber)))
    else:
        title = 'pydicom image'
    frame.master.title(title)
    photo_image = get_tkinter_photoimage_from_pydicom_image(data)
    #with Image.open(photo_image) as image:
     #   cover = resizeimage.resize_cover(image, [200, 100])
    #scale_w = 1#new_width/old_width
    #scale_h = 500#new_height/old_height
    #photo_image.zoom(scale_w)
    
    label = tkinter.Label(frame, image=photo_image, background='#000')
    label.config(width=500)
    label.config(height=500)

    # keep a reference to avoid disappearance upon garbage collection
    label.photo_reference = photo_image
    label.grid()
    frame.grid()

    #if block:
    #    frame.mainloop()
    return label

def dicom_to_array(filename):
    d = dicom.read_file(filename)
    a = d.pixel_array
    return np.array(a)


def read_info(file):
    RefDs = dicom.read_file(file)
    print(RefDs)
    return RefDs

def build_window():
    from Tkinter import *
    file = 'MAMMOGRAPHY_PRESENTATION.dcm'
    df = pydicom.read_file(file)
    head = read_info(file)
    

    ventana = Tk()
    ventana.title('DICOM Image Processing')

    label1=Label(ventana,text="prueba")
    label1.grid(row=1,column=2)

    label_image = show_image(df)
    label_image.grid(row=1,column=1)
    e = Entry(ventana)
    e.pack()
    e.grid(row=1, column=3)
    e.delete(0, END)
    e.insert(0, head.PatientName)

    '''
    f = Figure(figsize=(5,5), dpi=100)
    plt = f.add_subplot(111)
    #df = np.load('MAMMOGRAPHY_PRESENTATION.dcm')

    a1 = dicom_to_array('MAMMOGRAPHY_PRESENTATION.dcm')
    hist,bins = np.histogram(a1, bins=256)

    

    a1_eq = exposure.equalize_hist(a1)
    hist_eq,bins_eq = np.histogram(a1_eq, bins=256)

    #fig2 = plt.figure()
    #plt.imshow(a1_eq, cmap="gray", interpolation="bicubic")
    #plt.colorbar()
    #fig2.suptitle("Histogram equalization + Gray colormap", fontsize=12)


    #plt.hist(df.flatten(), bins=50, color='c')
    #plt.xlabel("Hounsfield Units (HU)")
    #plt.ylabel("Frequency")
    plt.plot()
    canvas = FigureCanvasTkAgg(f)
    canvas.show()
    canvas.get_tk_widget().pack(INSIDE=tkinter.TOP, fill=tkinter.BOTH, expand=True)

    '''
    ventana.mainloop()





        

if __name__ == '__main__':
    '''
    PM = PokerMachine()
    mainloop()
    '''
    build_window()
    