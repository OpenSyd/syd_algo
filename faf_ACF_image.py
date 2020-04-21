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

def convertNewParameterToFloat(newParameterString, size=1):
    if newParameterString is not None:
        parameterFloat = np.array(newParameterString.split(','))
        parameterFloat = parameterFloat.astype(np.float)
        if len(parameterFloat) == 1:
            parameterFloat = [parameterFloat[0].astype(np.float)]*size
        return parameterFloat
    else:
        return None

# -----------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)

@click.option('--ct', '-ct', help='Input CT filename', required=True,
                type=click.Path(dir_okay=False))
@click.option('--c', '-c', help='Attenuation Coefficient for Water and Bone for CT energy')
@click.option('--s', '-s', help='Attenuation Coefficient for Air, Water and Bone for SPECT energies')
@click.option('--weight', '-w', help='Weights for all emitted peak for the SPECT')
@click.option('--output', '-o', help='Output filename', required=True,
                type=click.Path(dir_okay=False,
                              writable=True, readable=False,
                              resolve_path=True, allow_dash=False, path_type=None))

def faf_ACF_image_click(ct, c, s, weight, output):
    '''
    Compute the Attenuation Correction Factor (ACF) image from the CT taking into account the energies of the CT acquisition (-c option) and of the emitted gamma (-s option) along the axis a.

    - -c: are the attenuation coefficients for water and bone for mean energy of the X-ray used for CT (2 expected values)

    - -s: are the attenuation coefficients for air, water and bone for all targeted energies of the SPECT

    - [-w] (optional). If radionuclide emits several peaks, w is used to weight them ; it should represent the relative contribution of detected gamma energy peaks.

    The attenuation coefficient can be found on:
    https://physics.nist.gov/PhysRefData/XrayMassCoef/tab4.html

    Radionuclide info: http://www.nucleide.org/DDEP_WG/DDEPdata.htm

    Example of linear attenuation coefficient: \n
    Radionuclide  Energy (keV)  Air         Water       Cortical Bone   Weight \n
    F18           511           0.00010402  0.09658967  0.16740534 \n
    I131          364.5         0.00011938  0.11080844  0.19272457 \n
    Tc99m         140.5         0.0001668   0.15459051  0.28497715 \n
    In111         171.28        0.00015653  0.14515948  0.26067691     0.6 \n
    In111         245.35        0.0001384   0.12842316  0.22564878     0.33 \n
    Lu177         112.95        0.00017856  0.16529103  0.31934538     0.062 \n
    Lu177         208.37        0.00014657  0.13597229  0.24070651     0.104 \n

    Example for CT energy 120 keV, ie. effective energy of 60 keV (around the half) \n
    Energy (keV)  Air         Water       Cortical Bone \n
    60            0.00022586  0.2068007   0.57384408 \n
    
    All the options can pe passed like that (in that order): \n
     faf_ACF_image -ct CT.mhd -c "cWater,cBone" -s "sAir1,sWater1,sBone1,sAir2,sWater2,sBone2" -w "w1,w2" -o ACF.mhd \n
    eg= faf_ACF_image -ct CT.mhd -c "0.2068007,0.57384408" -s "0.00015653,0.14515948,0.26067691,0.0001384,0.12842316,0.22564878" -w "0.6,0.33" -o ACF.mhd \n
    And the attenuation coefficient is computed from HU like that: \n
     if HU < 0: \n
       sWater + (sWater - sAir)/1000.0 * HU \n
     if HU > 0: \n
       sWater + (cBone - cWater)*(sBone - sWater)/1000.0 * HU \n
    
    Then, the AC are weighted and sum, Finally, the image is projected along axis y and the return result is (division by 10 because mm to cm and division by 2 because mean attenuation): \n
        exp(spacingAlongAxis/(2.0*10.0)*projectedAC)
    
    '''

    ctImage = itk.imread(ct)
    ctCoeff = convertNewParameterToFloat(c)
    spectCoeff = convertNewParameterToFloat(s)
    weightPeak = convertNewParameterToFloat(weight)
    outputImage = faf_ACF_image(ctImage, ctCoeff, spectCoeff, weightPeak)
    itk.imwrite(outputImage, output)

# -----------------------------------------------------------------------------
def faf_ACF_image(image, ctCoeff, spectCoeff, weight=None):

    if image.GetImageDimension() != 3:
        print("Image dimension (" + str(image.GetImageDimension()) + ") is not 3")
        sys.exit(1)
    if ctCoeff is None:
        print("ctCoeff is mandatory")
        sys.exit(1)
    elif len(ctCoeff) != 2:
        print("ctCoeff size (" + str(len(ctCoeff)) + ") is not 2")
        sys.exit(1)
    if weight is None:
        weight = [1]
    nbPeak = len(weight)
    if spectCoeff is None:
        print("spectCoeff is mandatory")
        sys.exit(1)
    elif len(spectCoeff) != 3*nbPeak:
        print("ctCoeff size (" + str(len(spectCoeff)) + ") is not 3*nbPeak (" + str(3*nbPeak) + ")")
        sys.exit(1)

    ctArray = itk.array_from_image(image)
    ctPositiveValueIndex = np.where(ctArray > 0)
    ctNegativeValueIndex = np.where(ctArray < 0)
    attenuation = np.zeros(ctArray.shape)
    for i in range(nbPeak):
        attenuationTemp = np.zeros(ctArray.shape)
        attenuationTemp[ctNegativeValueIndex] = spectCoeff[3*i+1] + (spectCoeff[3*i+1] - spectCoeff[3*i])/1000.0 *ctArray[ctNegativeValueIndex]
        attenuationTemp[ctPositiveValueIndex] = spectCoeff[3*i+1] + ctCoeff[0]/(ctCoeff[1]-ctCoeff[0])*(spectCoeff[3*i+2] - spectCoeff[3*i+1])/1000.0 *ctArray[ctPositiveValueIndex]
        attenuation = attenuation + weight[i]*attenuationTemp
    attenuation[attenuation < 0] = 0
    attenuationImage = itk.image_from_array(attenuation)
    attenuationImage.CopyInformation(image)
    
    projectionAxis = 1
    projection = image_projection.image_projection(attenuationImage, projectionAxis)
    acfArray = np.exp(image.GetSpacing()[projectionAxis]/(2.0*10.0)*itk.array_from_image(projection))
    acfImage = itk.image_from_array(acfArray)
    acfImage.CopyInformation(projection)
    flipFilter = itk.FlipImageFilter.New(Input=acfImage)
    flipFilter.SetFlipAxes((False, True))
    flipFilter.Update()
    acfImage = flipFilter.GetOutput()

    return acfImage

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    faf_ACF_image_click()

# -----------------------------------------------------------------------------
import unittest
import tempfile
import hashlib
import shutil
import os
import wget

class Test_Faf_ACF_Image_(unittest.TestCase):
    def test_faf_ACF_image(self):
        tmpdirpath = tempfile.mkdtemp()
        filenameMhd = wget.download("https://gitlab.in2p3.fr/OpenSyd/syd_tests/-/raw/master/dataTest/CT.mhd?inline=false", out=tmpdirpath, bar=None)
        filenameRaw = wget.download("https://gitlab.in2p3.fr/OpenSyd/syd_tests/-/raw/master/dataTest/CT.raw?inline=false", out=tmpdirpath, bar=None)
        ct = itk.imread(os.path.join(tmpdirpath, filenameMhd))

        output=faf_ACF_image(ct, [0.2068007, 0.57384408], [0.00014657, 0.13597229, 0.24070651])
        itk.imwrite(output, os.path.join(tmpdirpath, "testACF.mha"))
        with open(os.path.join(tmpdirpath, "testACF.mha"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("ba5a3f2e892fcd8eb95d5d2dc4034a2bbcac907b6da84ad78545801c38940d0f" == new_hash)
        shutil.rmtree(tmpdirpath)
