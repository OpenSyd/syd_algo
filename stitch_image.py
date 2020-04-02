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

@click.option('--input1', '-i', help='Input filename', required=True,
                type=click.Path(dir_okay=False))
@click.option('--input2', '-j', help='Input filename', required=True,
                type=click.Path(dir_okay=False))
@click.option('--dimension', '-d', default=2, help='Dimension for stitching (default 2)')
@click.option('--pad', '-p', default=0, help='Default value for padding (default 0)')
@click.option('--output', '-o', help='Output filename', required=True,
                type=click.Path(dir_okay=False,
                              writable=True, readable=False,
                              resolve_path=True, allow_dash=False, path_type=None))

def stitch_image_click(input1, input2, dimension, pad, output):
    '''
    Stitch 2 FOV images (input1 and input2) according their origin and size along the dimension d.
    Both input1 and input2 are images readible by ITK (eg: .mhd), usually 3D image from nuclear medecine.
    The output have the same spacing and origin than FOV1 image. The FOV2 image is resampled to be stitched along d. FOV1 image is considered to be the image with the littlest origin.
    The output is the copy the FOV1 and FOV2 values, except at the junction, if FOV1 > FOV2, take FOV1 (it avoid 0 values)

    unittest:
       python -m unittest stitch_image
    '''

    input1Image = itk.imread(input1)
    input2Image = itk.imread(input2)
    outputImage = stitch_image(input1Image, input2Image, dimension, pad)
    itk.imwrite(outputImage, output)

# -----------------------------------------------------------------------------
def stitch_image(image1, image2, dimension=2, pad=0):

    Dimension = image1.GetImageDimension()
    if image2.GetImageDimension() != Dimension:
        print("Image1 dimension (" + str(Dimension) + ") and Image2 dimension (" + str(image2.GetImageDimension()) + ") are different")
        sys.exit(1)

    #Check negative spacing or non identity direction
    if not (itk.array_from_matrix(image1.GetDirection()) == np.eye(Dimension)).all():
        image1 = gt.applyTransformation(image1, None, None, None, force_resample=True, pad=pad)
    if not (itk.array_from_matrix(image2.GetDirection()) == np.eye(Dimension)).all():
        image2 = gt.applyTransformation(image2, None, None, None, force_resample=True, pad=pad)

    #Determine the FOV1image and FOV2image
    if image1.GetOrigin()[dimension] > image2.GetOrigin()[dimension]:
        FOV1image = image2
        FOV2image = image1
    else:
        FOV1image = image1
        FOV2image = image2

    #Determine dimension for resampled FOV2
    lowFOV2index = itk.ContinuousIndex[itk.D, Dimension]()
    for i in range(Dimension):
        lowFOV2index[i] = -0.5
    lowFOV2point = FOV2image.TransformContinuousIndexToPhysicalPoint(lowFOV2index)
    lowFOV2index = FOV1image.TransformPhysicalPointToIndex(lowFOV2point)
    lowFOV2point = FOV1image.TransformIndexToPhysicalPoint(lowFOV2index)
    highFOV2index = itk.ContinuousIndex[itk.D, Dimension]()
    for i in range(Dimension):
        highFOV2index[i] = FOV2image.GetLargestPossibleRegion().GetSize()[i] -0.5
    highFOV2point = FOV2image.TransformContinuousIndexToPhysicalPoint(highFOV2index)
    highFOV2index = FOV1image.TransformPhysicalPointToIndex(highFOV2point)
    newFOV2Origin = [0]*Dimension
    for i in range(Dimension):
        newFOV2Origin[i] = FOV1image.GetOrigin()[i]
    newFOV2Origin[dimension] = lowFOV2point[dimension]
    newFOV2Size = [0]*Dimension
    for i in range(Dimension):
        newFOV2Size[i] = FOV1image.GetLargestPossibleRegion().GetSize()[i]
    newFOV2Size[dimension] = highFOV2index[dimension] - lowFOV2index[dimension] +1

    #Resample FOV2image to be aligned with FOV1image
    resampledFOV2image = gt.applyTransformation(FOV2image, None, FOV1image, None, newsize=newFOV2Size, neworigin=newFOV2Origin, force_resample=True, pad=pad)

    #Determine size of the output
    outputLastIndex = itk.Index[Dimension]()
    for i in range(Dimension):
        outputLastIndex[i] = resampledFOV2image.GetLargestPossibleRegion().GetSize()[i] -1
    outputLastPoint = resampledFOV2image.TransformIndexToPhysicalPoint(outputLastIndex)
    outputLastIndex = FOV1image.TransformPhysicalPointToIndex(outputLastPoint)
    outputSize = itk.Size[Dimension]()
    for i in range(Dimension):
        outputSize[i] = FOV1image.GetLargestPossibleRegion().GetSize()[i]
    outputSize[dimension] = outputLastIndex[dimension] +1

    #Create output
    ImageType = itk.Image[itk.template(image1)[1][0], Dimension]
    outputImage = ImageType.New()
    outputStart = itk.Index[Dimension]()
    for i in range(Dimension):
        outputStart[i] = 0
    outputRegion = itk.ImageRegion[Dimension]()
    outputRegion.SetSize(outputSize)
    outputRegion.SetIndex(outputStart)
    outputImage.SetRegions(outputRegion)
    outputImage.Allocate()
    outputImage.FillBuffer(pad)
    outputImage.SetSpacing(FOV1image.GetSpacing())
    outputImage.SetDirection(FOV1image.GetDirection())
    outputImage.SetOrigin(FOV1image.GetOrigin())
    
    #Fill the output with resampledFOV2image to begin
    outputArrayView = itk.array_view_from_image(outputImage)
    resampledFOV2ArrayView = itk.array_view_from_image(resampledFOV2image)
    FOV1ArrayView = itk.array_view_from_image(FOV1image)
    outputBeginFOV2Index = itk.Index[Dimension]()
    for i in range(Dimension):
        outputBeginFOV2Index[i] = 0
    outputBeginFOV2Point = resampledFOV2image.TransformIndexToPhysicalPoint(outputBeginFOV2Index)
    outputBeginFOV2Index = outputImage.TransformPhysicalPointToIndex(outputBeginFOV2Point)
    outputArrayView[outputBeginFOV2Index[2]:,outputBeginFOV2Index[1]:,outputBeginFOV2Index[0]:] = resampledFOV2ArrayView[:]
    
    #Fill the output with FOV1image where it's superior to current output (to avoid artifact)
    outputEndFOV1Index = itk.Index[Dimension]()
    for i in range(Dimension):
        outputEndFOV1Index[i] = FOV1image.GetLargestPossibleRegion().GetSize()[i]
    outputArrayView[np.where(FOV1ArrayView > outputArrayView[:outputEndFOV1Index[2],:outputEndFOV1Index[1],:outputEndFOV1Index[0]])] = FOV1ArrayView[np.where(FOV1ArrayView > outputArrayView[:outputEndFOV1Index[2],:outputEndFOV1Index[1],:outputEndFOV1Index[0]])]
    return outputImage

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    stitch_image_click()



# -----------------------------------------------------------------------------
import unittest
import tempfile
import hashlib
import shutil
import os

class Test_Stitch_Image(unittest.TestCase):
    def test_stitch_image(self):
        x = np.arange(0, 23, 1)
        y = np.arange(20, 40, 1)
        z = np.arange(0, 27, 1)
        xx, yy, zz = np.meshgrid(x, y, z)
        image1 = itk.image_from_array(np.int16(xx))
        image1.SetOrigin([7, 3.4, 30])
        image1.SetSpacing([2, 2, 2])

        x = np.arange(0, 23, 1)
        y = np.arange(0, 30, 1)
        z = np.arange(0, 27, 1)
        xx, yy, zz = np.meshgrid(x, y, z)
        image2 = itk.image_from_array(np.int16(xx))
        image2.SetOrigin([7, 3.4, -10])
        image2.SetSpacing([2, 2, 2])

        output=stitch_image(image1, image2, dimension=2, pad=0)
        tmpdirpath = tempfile.mkdtemp()
        itk.imwrite(output, os.path.join(tmpdirpath, "testStitch.mha"))
        with open(os.path.join(tmpdirpath, "testStitch.mha"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("89d8c32d1482b4b582ccfdfe824881ccbdffe5a3dbfca9a8e101b882c79bb41c" == new_hash)
        shutil.rmtree(tmpdirpath)
