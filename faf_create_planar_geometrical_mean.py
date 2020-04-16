#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): OpenGATE Collaboration
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE.md for further details
# -----------------------------------------------------------------------------

import gatetools as gt
import itk
import click
import numpy as np
import sys


# -----------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)

@click.option('--input', '-i', help='Input WB filename', required=True,
                type=click.Path(dir_okay=False))
@click.option('--output', '-o', help='Output filename', required=True,
                type=click.Path(dir_okay=False,
                              writable=True, readable=False,
                              resolve_path=True, allow_dash=False, path_type=None))

def faf_create_planar_geometrical_mean_click(input, output):
    '''
    Take the whole body planar SPECT image and compute the geometrical mean of this image
    The slice ordre of the image must be like that:
     - Head 1
     - Head 2
     - Scatter Head 1
     - Scatter Head 2
    '''

    inputImage = itk.imread(input)
    outputImage = faf_create_planar_geometrical_mean(inputImage)
    itk.imwrite(outputImage, output)

# -----------------------------------------------------------------------------
def faf_create_planar_geometrical_mean(image):

    if image.GetImageDimension() != 3:
        print("Image dimension (" + str(image.image.GetImageDimension()) + ") is not 3")
        sys.exit(1)
    if image.GetLargestPossibleRegion().GetSize()[2] != 4:
        print("Image size (" + str(image.GetLargestPossibleRegion().GetSize()[2]) + ") is not 4")
        sys.exit(1)
    
    array = (itk.array_from_image(image)).astype(float)
    arrayAnt = array[0, :, :] - 1.1*array[2, :, :]
    arrayPost = array[1, :, :] - 1.1*array[3, :, :]
    arrayPost = np.flip(arrayPost, 1)
    
    arrayAnt[arrayAnt < 0] = 0
    arrayPost[arrayPost < 0] = 0
    
    outputArray = np.sqrt(arrayAnt*arrayPost)
    outputImage = itk.image_from_array(outputArray)
    spacing =  np.array(image.GetSpacing())
    spacing = np.delete(spacing, 2)
    outputImage.SetSpacing(spacing)
    origin =  np.array(image.GetOrigin())
    origin = np.delete(origin, 2)
    outputImage.SetOrigin(origin)
    return outputImage

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    faf_create_planar_geometrical_mean_click()

# -----------------------------------------------------------------------------
import unittest
import tempfile
import hashlib
import shutil
import os

class Test_Faf_Create_Planar_Geometrical_Mean(unittest.TestCase):
    def test_faf_create_planar_geometrical_mean(self):
        x = np.arange(0, 23, 1)
        y = np.arange(20, 41, 1)
        xx, yy = np.meshgrid(x, y)
        array = np.zeros([4, 21, 23])
        xx = np.int16(xx)
        xxFlip = np.flip(xx, 1)
        array[0, :, :] = xx
        array[1, :, :] = xxFlip
        array[2, :, :] = 0.5*xx
        array[3, :, :] = 0.5*xxFlip
        
        image = itk.image_from_array(array)

        output=faf_create_planar_geometrical_mean(image)
        outputArray = itk.array_view_from_image(output)
        self.assertTrue(outputArray[13, 5] == np.sqrt((5-1.1*0.5*5)**2))

