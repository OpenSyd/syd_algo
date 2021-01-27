#!/usr/bin/env python

import numpy as np
import click
import itk


#------------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_options=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--input','-i', 'input_file', help='Input mhd projection file')
@click.option('--output','-o','output_file',help='Output mhd file with scatter corrected projection')

def scatter_correction_dewClick(input_file, output_file):
    '''
    Compute the scatter correction in a cas of a double energy window for mhd projection and save the result in a mhd file. The user need to specify the energy limits for the main window and for the scatter window.
    '''
    scatter_correction_dew(input_file, output_file)

def scatter_correction_dew(input_file, output_file):

    image = itk.imread(input_file)
    array = (itk.array_from_image(image)).astype(float)
    nb_energy_window = 2
    nb_energy = 2*nb_energy_window
    nb_angle = int(array.shape[0] /(2*nb_energy))

    array_head1_energy1 = array[0:nb_angle,:,:] - 1*1*array[2*nb_angle:3*nb_angle,:,:]
    array_head1_energy2 = array[4*nb_angle:5*nb_angle,:,:] - 1.1*array[6*nb_angle:7*nb_angle,:,:]
    array_head2_energy1 = array[nb_angle:2*nb_angle,:,:] - 1*1*array[3*nb_angle:4*nb_angle,:,:]
    array_head2_energy2 = array[5*nb_angle:6*nb_angle,:,:] - 1.1*array[7*nb_angle:8*nb_angle,:,:]

    array_head1_energy1[array_head1_energy1 < 0] = 0
    array_head1_energy2[array_head1_energy2 < 0] = 0
    array_head2_energy1[array_head2_energy1 < 0] = 0
    array_head2_energy2[array_head2_energy2 < 0] = 0

    array_head1 = np.concatenate((array_head1_energy1,array_head1_energy2))
    array_head2 = np.concatenate((array_head2_energy1,array_head2_energy2))
    itkimg= np.stack(array_head1 + array_head2)
    itkimg = itk.image_from_array(itkimg)
    itk.imwrite(itkimg, output_file)


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
        scatter_correction_dew(filenameMhd, output)
