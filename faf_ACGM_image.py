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


# -----------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)

@click.option('--gm', '-gm', help='Input registered Geometrical Mean Planar Image filename', required=True, type=click.Path(dir_okay=False))
@click.option('--acf', '-acf', help='Input Attenuation Coefficient Factor Image filename', required=True, type=click.Path(dir_okay=False))
@click.option('--factor', '-f', help='Factor used for the pixel in GM that are outside the ACF field of view', default=4.168696975)
@click.option('--output', '-o', help='Output filename', required=True,
                type=click.Path(dir_okay=False,
                              writable=True, readable=False,
                              resolve_path=True, allow_dash=False, path_type=None))

def faf_ACGM_image_click(gm, acf, factor, output):
    '''
    Multiply the registered Geometrical Mean (GM) image by the Attenuation Correction Factor (ACF) image. Images must be in the same reference frame.

    - [gm]  is the output of faf_register_planar_image.py\n
    - [ACF_image] is the output of faf_ACF_image.py\n
    - <factor> is the factor used for the pixel in GM that are outside the ACF field of view.

    '''

    gmImage = itk.imread(gm)
    acfImage = itk.imread(acf)
    outputImage = faf_ACGM_image(gmImage, acfImage, factor)
    itk.imwrite(outputImage, output)

# -----------------------------------------------------------------------------
def faf_ACGM_image(gm, acf, factor=4.168696975):

    if gm.GetImageDimension() != 2:
        print("gm image dimension (" + str(gm.GetImageDimension()) + ") is not 2")
        sys.exit(1)

    if acf.GetImageDimension() != 2:
        print("acf image dimension (" + str(acf.GetImageDimension()) + ") is not 2")
        sys.exit(1)

    resampleACF = gt.applyTransformation(input=acf, like=gm, force_resample=True, pad=-1)

    resampleACFArray = itk.array_from_image(resampleACF)
    gmArray = itk.array_from_image(gm)
    acgmArray = np.zeros(gmArray.shape)
    negativeACFIndex = np.where(resampleACFArray == -1)
    positiveACFIndex = np.where(resampleACFArray != -1)
    acgmArray[negativeACFIndex] = factor*gmArray[negativeACFIndex]
    acgmArray[positiveACFIndex] = resampleACFArray[positiveACFIndex]*gmArray[positiveACFIndex]

    acgmImage = itk.image_from_array(acgmArray)
    acgmImage.CopyInformation(gm)
    return acgmImage

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    faf_ACGM_image_click()

# -----------------------------------------------------------------------------
import unittest

class Test_Faf_ACGM_Image_(unittest.TestCase):
    def test_faf_ACGM_image(self):
        gm = np.ones((10,30))*11.2
        acf = np.ones((7,21))*3.3
        gmImage = itk.image_from_array(gm)
        gmImage.SetOrigin(np.array([2.3, -1.7]))
        acfImage = itk.image_from_array(acf)
        acfImage.SetOrigin(np.array([4.1, -0.9]))
        acgmImage = faf_ACGM_image(gmImage, acfImage)
        acgmArray = itk.array_from_image(acgmImage)

        self.assertTrue(acgmImage.GetLargestPossibleRegion().GetSize()[0] == 30)
        self.assertTrue(acgmImage.GetLargestPossibleRegion().GetSize()[1] == 10)
        self.assertTrue(acgmArray[1,1] == 11.2*4.168696975)
        self.assertTrue(np.allclose(acgmArray[4,12], 11.2*3.3))
