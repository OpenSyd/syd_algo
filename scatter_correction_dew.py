#!/usr/bin/env python3

import numpy as np
import click
import itk


#------------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_options=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--input','-i', 'input_image', help='Input mhd projection file')
@click.option('--head','head',default=2, help='Number of detectors')
@click.option('--angles','angles',help='Number of angles of one detector')
@click.option('--primary_window','-pw','primary_window',type=(int,int),help='Indexes of the primary window')
@click.option('--scatter_window','-sw','scatter_window',type=(int,int),help='Indexes of the scatter window')
@click.option('--factor','-f','factor',default=1.1,help='Multiplying factor')

def scatter_correction_dewClick(input_image,head,angles,primary_window,scatter_window,factor):
    '''
    Compute the scatter correction in a cas of a double energy window for mhd projection and save the result in a mhd file. The user need to specify the energy limits for the main window and for the scatter window.
    '''
    scatter_correction_dew(input_image,head,angles,primary_window,scatter_window,factor)

def scatter_correction_dew(input_image,head,angles,primary_window,scatter_window,factor):

    array = (itk.array_from_image(input_image)).astype(float)
    size = angles * len(primary_window)*len(scatter_window)*head
    if size != array.shape[0]:
        print('There is a difference beteween the calculated number of slice and the actual one')
        return []

    pw1 = primary_window[0]
    pw2 = primary_window[1]
    sw1 = scatter_window[0]
    sw2 =  scatter_window[1]
    array_res=[]
    
    for i in range(head):
        k = head*angles
        array_energy1 = array[k*pw1:k*(pw1+1),:,:] - factor*array[sw1*k:(sw1+1)*k,:,:]
        array_energy2 = array[k*pw2:k*(pw2+1),:,:] - factor*array[k*sw2:(sw2+1)*k,:,:]
        array_energy1[array_energy1 < 0] = 0
        array_energy2[array_energy2 < 0] = 0
        array_res=np.concatenate((array_energy1, array_energy2))

    itkimg = itk.image_from_array(array_res)
    
    return itkimg


# -----------------------------------------------------------------------------
if __name__=='main':
    scatter_correction_dewClick()

# -----------------------------------------------------------------------------
import unittest
import tempfile
import shutil
import os
import wget
import json

def createImageExample():
    x = np.arange(0,128,1)
    y = np.arange(0,120,1)
    z = np.arange(-0,128,1)
    xx, yy, zz = np.meshgrid(x, y, z)
    image = itk.image_from_array(np.int16(xx))
    image.SetOrigin([7, 3.4, -4.6])
    image.SetSpacing([4, 2, 3.6])
    return image


class Test_scatter_correction_dew_(unittest.TestCase):
    def test_scatter_correction_dew(self):
        tmpdirpath = tempfile.mkdtemp()
        image = createImageExample()
        array = itk.array_from_image(image)
        p1 = array[0][64][64]
        p2 = array[15][64][64]

        output = os.path.join(tmpdirpath, 'im_corrected.mhd')
        res = scatter_correction_dew(image, 2,15,[0,2],[1,3],1.1)
        res_array = itk.array_from_image(res)
        self.assertTrue(res.shape == (60,128,128))
        self.assertTrue(res_array[0][64][64] == 0.0)
        shutil.rmtree(tmpdirpath)
