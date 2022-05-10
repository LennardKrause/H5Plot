import os, argparse, h5py, hdf5plugin
import numpy as np
import pyqtgraph as pg

# H5ShowCube
# a tool to show h5 3d data without loading all data
#
# 3d: img_view.getImageItem().image.shape
# 2d: img_view.image.shape
#
# What it does:
# initialize as 3d cube
#  - img_view.setImage(np.zeros((inum,5,5)))
# fix color levels and histogram boundaries
#  - img_view.setLevels(0, data.mean()*25)
#  - img_view.setHistogramRange(0, data.mean()*30)
# force emit image change to load one 2d image
#  - img_view.timeLine.sigPositionChanged.emit(img_view.timeLine)
# reset range to full 2d data
#  - img_view.autoRange()
# update only the 2d image data
#  - img_view.getImageItem().setImage(data, autoHistogramRange=False, autoRange=False, autoLevels=False)
# PyQtGraph gets confused so we need to reset the histogram range
#   img_view.getHistogramWidget().setHistogramRange(*img_view.getImageItem().getLevels())

def init_parser():
    parser = argparse.ArgumentParser(description = '')
    parser.add_argument('-f', required=False, dest='_FILE', type=str, default='/Volumes/Nat_Uorg/MCH/DATA_beamtimes/2021_09_DanMAX/2ndDownload/2021092908/raw/SFO_AC_150Ks/scan-0323_pilatus.h5', help='path to file')
    return parser.parse_args()

def change_image():
    # where are we in time?
    current_idx = int(round(img_view.timeLine.value(),0))
    # pick only the slice we need
    with h5py.File(h5file, 'r') as h5f:
        data = h5f['entry/instrument/pilatus/data'][current_idx,:,:]
    # update the 2d image data
    img_view.getImageItem().setImage(data, autoHistogramRange=False, autoRange=False, autoLevels=False)
    # force reset the histogram range
    img_view.getHistogramWidget().setHistogramRange(*img_view.getImageItem().getLevels())
    # update the label
    label.setText(f'{iname} {current_idx}')

def imageHoverEvent(point):
    # get the index
    current_idx = int(round(img_view.timeLine.value(),0))
    # map it
    p = img_view.getView().mapSceneToView(point)
    x = int(np.clip(p.x(), 0, img_view.getImageItem().image.shape[1] - 1))
    y = int(np.clip(p.y(), 0, img_view.getImageItem().image.shape[0] - 1))
    # get the value from the *2d image* (not img_view.image[x,y])
    v = img_view.getImageItem().image[y,x]
    # update the label
    label.setText(f'{iname} {current_idx} {x:>4} {y:>4}: {v}')

def main():
    # set globals
    # imageHoverEvent and change_image need:
    #  - to access ImageView (img_view)
    #  - to access TextItem (label)
    #  - to access h5 file (h5file)
    #  - to get the h5 name (iname)
    global img_view, label, h5file, iname

    _ARGS = init_parser()
    h5file = _ARGS._FILE
    iname = os.path.splitext(os.path.basename(h5file))[0]

    pg.setConfigOptions(imageAxisOrder='row-major', background='k', leftButtonPan=True)
    app = pg.mkQApp()

    # define grid layout
    layout = pg.QtWidgets.QGridLayout()
    
    # make a widget, set the layout
    centralwidget = pg.QtWidgets.QWidget()
    centralwidget.setLayout(layout)
    
    # build a window, put the widget
    win = pg.QtWidgets.QMainWindow()
    win.resize(1024,1024)
    win.setWindowTitle(h5file)
    win.setCentralWidget(centralwidget)
    
    # init ImageView
    img_view = pg.ImageView()
    layout.addWidget(img_view, 0, 0)
    # set colormap
    img_view.setPredefinedGradient('magma')
    # hide ui buttons
    img_view.ui.roiBtn.hide()
    img_view.ui.menuBtn.hide()
    # connect to custom signals
    img_view.scene.sigMouseMoved.connect(imageHoverEvent)
    img_view.timeLine.sigPositionChanged.connect(change_image)
    
    # add a label to show name, index, x, y and value
    label = pg.TextItem(iname)
    label.setFont(pg.QtGui.QFont('Helvetica', 12, weight=100))
    img_view.scene.addItem(label)

    # get number of images from h5 file
    # load first image
    with h5py.File(h5file, 'r') as h5f:
        inum = h5f['entry/instrument/pilatus/data'].shape[0]
        data = h5f['entry/instrument/pilatus/data'][0,:,:]

    # initialize ImageView with empty 3d cube
    # first dimension must be the number of images
    # 2nd and 3rd as small as possible to save memory
    # 5 is minimum for PyQtGraph to recognize 3d cube data
    img_view.setImage(np.zeros((inum,5,5)))
    
    # set color levels and histogram ranges to keep them steady
    img_view.setLevels(0, data.mean()*25)
    img_view.setHistogramRange(0, data.mean()*30)

    win.show()
    # update the image -> insert 2d image
    img_view.timeLine.sigPositionChanged.emit(img_view.timeLine)
    # call auto range on 2d image to get the correct bounds
    img_view.autoRange()

    pg.mkQApp().exec_()

if __name__ == '__main__':
    main()
