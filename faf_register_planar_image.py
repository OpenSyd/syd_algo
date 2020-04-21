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
import image_projection


# -----------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)

@click.option('--planar', '-p', help='Input geometrical mean planar 2D image filename', required=True,
                type=click.Path(dir_okay=False))
@click.option('--spect', '-s', help='Input SPECT 3D image filename', required=True,
                type=click.Path(dir_okay=False))
@click.option('--output', '-o', help='Output filename for the geometrical mean registered 2D image', required=True,
                type=click.Path(dir_okay=False,
                              writable=True, readable=False,
                              resolve_path=True, allow_dash=False, path_type=None))

def faf_register_planar_image_click(planar, spect, output):
    '''
    Register the geometrical mean planar image (usually the output of faf_create_planar_geometrical_mean) on the projected SPECT 3D image along the y coordinate.
    '''

    inputPlanar = itk.imread(planar)
    inputSpect = itk.imread(spect)
    outputImage = faf_register_planar_image(inputPlanar, inputSpect)
    itk.imwrite(outputImage, output)

# -----------------------------------------------------------------------------
def faf_register_planar_image(planar, spect):

    if planar.GetImageDimension() != 2:
        print("Planar image dimension (" + str(planar.GetImageDimension()) + ") is not 2")
        sys.exit(1)
    if spect.GetImageDimension() != 3:
        print("Planar image dimension (" + str(spect.GetImageDimension()) + ") is not 3")
        sys.exit(1)

    projectedSpect = image_projection.image_projection(spect, 1)
    flipFilter = itk.FlipImageFilter.New(Input=projectedSPECT)
    flipFilter.SetFlipAxes((False, True))
    flipFilter.Update()
    projectedSPECT = flipFilter.GetOutput()
    projectedSpect = gt.applyTransformation(input=projectedSpect, spacinglike=planar, force_resample=True, adaptive=True)

    minCorrelation = 10
    minCorrelationIndex = 0

    for i in range(projectedSpect.GetLargestPossibleRegion().GetSize()[1] + planar.GetLargestPossibleRegion().GetSize()[1] -1):
        newOrigin = itk.Vector[itk.D, 2]()
        newOrigin[0] = projectedSpect.GetOrigin()[0] + (projectedSpect.GetLargestPossibleRegion().GetSize()[0] -  planar.GetLargestPossibleRegion().GetSize()[0])*projectedSpect.GetSpacing()[0]/2.0
        newOrigin[1] = projectedSpect.GetOrigin()[1] - (planar.GetLargestPossibleRegion().GetSize()[1] -1 -i)*projectedSpect.GetSpacing()[1]
        centeredPlanar = gt.applyTransformation(input=planar, neworigin=newOrigin)
        centredPlanarOriginInProjectedSpect = projectedSpect.TransformPhysicalPointToIndex(newOrigin)

        identityTransform = itk.IdentityTransform[itk.D, 2].New()
        identityTransform.SetIdentity()
        interpolator = itk.LinearInterpolateImageFunction[type(planar), itk.D].New()

        smallRegion = itk.ImageRegion[2]()
        smallRegionSize = itk.Size[2]()
        smallRegionSize[0] = min(centeredPlanar.GetLargestPossibleRegion().GetSize()[0], projectedSpect.GetLargestPossibleRegion().GetSize()[0])
        smallRegionSize[1] = min(i + 1, projectedSpect.GetLargestPossibleRegion().GetSize()[1] + planar.GetLargestPossibleRegion().GetSize()[1] -1 -i, projectedSpect.GetLargestPossibleRegion().GetSize()[1])
        smallRegion.SetSize(smallRegionSize)
        smallRegionIndex = itk.Index[2]()
        smallRegionIndex[0] = max(0, centredPlanarOriginInProjectedSpect[0])
        smallRegionIndex[1] = max(0, centredPlanarOriginInProjectedSpect[1])
        smallRegion.SetIndex(smallRegionIndex)

        miCoeffFilter = itk.MattesMutualInformationImageToImageMetric[type(planar), type(planar)].New()
        miCoeffFilter.SetMovingImage(centeredPlanar)
        miCoeffFilter.SetFixedImage(projectedSpect)
        miCoeffFilter.SetTransform(identityTransform)
        miCoeffFilter.SetInterpolator(interpolator)
        miCoeffFilter.SetFixedImageRegion(smallRegion)
        miCoeffFilter.UseAllPixelsOn()
        miCoeffFilter.SetNumberOfHistogramBins(50)
        miCoeffFilter.ReinitializeSeed()
        miCoeffFilter.Initialize()
        if miCoeffFilter.GetValue(identityTransform.GetParameters()) < minCorrelation:
            minCorrelation = miCoeffFilter.GetValue(identityTransform.GetParameters())
            minCorrelationIndex = i

    newOrigin = itk.Vector[itk.D, 2]()
    newOrigin[0] = projectedSpect.GetOrigin()[0] + (projectedSpect.GetLargestPossibleRegion().GetSize()[0] -  planar.GetLargestPossibleRegion().GetSize()[0])*projectedSpect.GetSpacing()[0]/2.0
    newOrigin[1] = projectedSpect.GetOrigin()[1] - (planar.GetLargestPossibleRegion().GetSize()[1] -1 -minCorrelationIndex)*projectedSpect.GetSpacing()[1]
    centeredPlanar = gt.applyTransformation(input=planar, neworigin=newOrigin)

    return centeredPlanar

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    faf_register_planar_image_click()

# -----------------------------------------------------------------------------
import unittest
import tempfile
import hashlib
import shutil
import os

#class Test_Faf_Register_Planar_Image(unittest.TestCase):
#    def test_faf_register_planar_image(self):
#        x1 = np.arange(0, 23, 1)
#        y1 = np.arange(0, 71, 1)
#        xx1, yy1 = np.meshgrid(x1, y1)
#        xx1 = np.int16(xx1)
#        image1 = itk.image_from_array(array)

#        output=faf_register_planar_image(image1, )
#        outputArray = itk.array_view_from_image(output)
#        self.assertTrue(outputArray[13, 5] == np.sqrt((5-1.1*0.5*5)**2))

