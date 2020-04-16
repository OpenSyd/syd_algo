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

@click.option('--input', '-i', help='Input image filename', required=True,
                type=click.Path(dir_okay=False))
@click.option('--axis', '-p', help='Axis of the projection', default=0)
@click.option('--mean', '-m', help='Compute the mean of the projected image', is_flag=True)
@click.option('--output', '-o', help='Output filename', required=True,
                type=click.Path(dir_okay=False,
                              writable=True, readable=False,
                              resolve_path=True, allow_dash=False, path_type=None))

def image_projection_click(input, axis, mean, output):
    '''
    Project the input along the axis. Compute the mean of the projection along this axis if the flag is set
    '''

    inputImage = itk.imread(input)
    outputImage = faf_create_planar_geometrical_mean(inputImage, axis, mean)
    itk.imwrite(outputImage, output)

# -----------------------------------------------------------------------------
def image_projection(image, axis=0, mean=False):
    
    array = (itk.array_from_image(image)).astype(float)
    if image.GetImageDimension() == 3:
        array = np.swapaxes(array, 0, 2)
    projectedArray = np.sum(array, axis)
    
    if mean:
        projectedArray = projectedArray / image.GetLargestPossibleRegion().GetSize()[axis]

    outputImage = itk.image_from_array(projectedArray)
    spacing =  np.array(image.GetSpacing())
    spacing = np.delete(spacing, axis)
    outputImage.SetSpacing(spacing)
    origin =  np.array(image.GetOrigin())
    origin = np.delete(origin, axis)
    outputImage.SetOrigin(origin)
    return outputImage

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    image_projection_click()

# -----------------------------------------------------------------------------
import unittest
import os

def createImageExample():
    x = np.arange(0, 23, 1)
    y = np.arange(20, 41, 1)
    z = np.arange(10, 25, 1)
    xx, yy, zz = np.meshgrid(x, y, z)
    image = itk.image_from_array(np.int16(xx))
    image.SetSpacing([1.1, 2, 3.1])
    image.SetOrigin([10, 12.4, -0.7])
    return image

class Test_Image_Projection(unittest.TestCase):
    def test_image_projection(self):
        image = createImageExample()
        output=image_projection(image, 0, False)
        outputArray = itk.array_view_from_image(output)
        self.assertTrue(outputArray[13, 14] == 14*15)
        self.assertTrue(output.GetSpacing()[0] == 2)
        self.assertTrue(output.GetSpacing()[1] == 3.1)
        self.assertTrue(output.GetOrigin()[0] == 12.4)
        self.assertTrue(output.GetOrigin()[1] == -0.7)
        self.assertTrue(output.GetLargestPossibleRegion().GetSize()[0] == 23)
        self.assertTrue(output.GetLargestPossibleRegion().GetSize()[1] == 21)
        output=image_projection(image, 1, False)
        outputArray = itk.array_view_from_image(output)
        self.assertTrue(outputArray[8, 5] == 253)
        self.assertTrue(output.GetSpacing()[0] == 1.1)
        self.assertTrue(output.GetSpacing()[1] == 3.1)
        self.assertTrue(output.GetOrigin()[0] == 10)
        self.assertTrue(output.GetOrigin()[1] == -0.7)
        self.assertTrue(output.GetLargestPossibleRegion().GetSize()[0] == 15)
        self.assertTrue(output.GetLargestPossibleRegion().GetSize()[1] == 21)
        output=image_projection(image, 2)
        outputArray = itk.array_view_from_image(output)
        self.assertTrue(outputArray[6, 10] == 6*21)
        self.assertTrue(output.GetSpacing()[0] == 1.1)
        self.assertTrue(output.GetSpacing()[1] == 2)
        self.assertTrue(output.GetOrigin()[0] == 10)
        self.assertTrue(output.GetOrigin()[1] == 12.4)
        self.assertTrue(output.GetLargestPossibleRegion().GetSize()[0] == 15)
        self.assertTrue(output.GetLargestPossibleRegion().GetSize()[1] == 23)
        output=image_projection(image, 2, True)
        outputArray = itk.array_view_from_image(output)
        self.assertTrue(outputArray[6, 10] == 6)

