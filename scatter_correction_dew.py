#!/usr/bin/env python3

import numpy as np
import click
import itk


#------------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_options=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--input','-i', 'input_image', help='Input mhd projection file')
@click.option('--head',default=2, help='Number of detectors')
@click.option('--angles',help='Number of angles of one detector')
@click.option('--primary_window','-pw',type=(int,int),help='Indexes of the primary window')
@click.option('--scatter_window','-sw',type=(int,int),help='Indexes of the scatter window')

def scatter_correction_dewClick(input_image,head,angles,primary_window,scatter_window):
    '''
    Compute the scatter correction in a cas of a double energy window for mhd projection and save the result in a mhd file. The user need to specify the energy limits for the main window and for the scatter window.
    '''
    scatter_correction_dew(input_image,head,angles,primary_window,scatter_window)

def scatter_correction_dew(input_image,head,angles,primary_window,scatter_window):

    array = (itk.array_from_image(input_image)).astype(float)
    size = angles * len(primary_window)*len(scatter_window)*head
    if size != array.shape[0]:
        print('There is a difference beteween the calculated number of slice and the actual one')
        return []

    pw1 = primary_window[0]
    pw2 = primary_window[1]
    sw1 = scatter_window[0]
    sw2 =  scatter_window[1]
    array_res = []
    
    for i in range(head):
        k = head*angles
        array_energy1 = array[k*pw1:k*(pw1+1),:,:] - 1*1*array[sw1*k:(sw1+1)*k,:,:]
        array_energy2 = array[k*pw2:k*(pw2+1),:,:] - 1.1*array[k*sw2:(sw2+1)*k,:,:]
        array_energy1[array_energy1 < 0] = 0
        array_energy2[array_energy2 < 0] = 0
        array_res.append((array_energy1, array_energy2))

    

    #array_head1 = np.concatenate((array_head1_energy1,array_head1_energy2))
    #array_head2 = np.concatenate((array_head2_energy1,array_head2_energy2))
    #itkimg= np.stack(array_head1 + array_head2)
    #itkimg = itk.image_from_array(itkimg)
    
    #return itkimg


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

class Test_scatter_correction_dew_(unittest.TestCase):
    def test_scatter_correction_dew(self):
        tmpdirpath = tempfile.mkdtemp()
        filenameMhd = wget.download("https://gitlab.in2p3.fr/OpenSyd/syd_tests/-/raw/master/dataTest/fantome_sans_correction.mhd?inline=false", out=tmpdirpath, bar=None)
        filenameRaw = wget.download("https://gitlab.in2p3.fr/OpenSyd/syd_tests/-/raw/master/dataTest/fantome_sans_correction.raw?inline=false", out=tmpdirpath, bar=None)

        output = os.path.join(tmpdirpath, 'im_corrected.mhd')
        img = itk.imread(filenameMhd)
        res = scatter_correction_dew(img, 2,15,[0,2],[1,3])
        self.assertTrue(res != [])
        shutil.rmtree(tmpdirpath)
