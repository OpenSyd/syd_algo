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
import image_projection


# -----------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)

@click.option('--spect', '-s', help='Input SPECT Image filename', required=True, type=click.Path(dir_okay=False))
@click.option('--acgm', '-acgm', help='Input Attenuation Corrected Geometrical Mean Image filename', required=True, type=click.Path(dir_okay=False))
@click.option('--injected_activity', '-a', help='Injected activity for the SPECT in MBq', required=True, default=1.0)
@click.option('--half_life', '-l', help='Half life for the injected radionuclide in the SPECT in h', required=True, default=6.0)
@click.option('--delta_time', '-t', help='Time between injection and beginning of the SPECT acquisition in h', required=True, default=1.0)
@click.option('--acquisition_duration', '-d', help='Total duration time of the SPECT acquisition in s', required=True, default=900.0)
@click.option('--output', '-o', help='Output filename', required=True,
                type=click.Path(dir_okay=False,
                              writable=True, readable=False,
                              resolve_path=True, allow_dash=False, path_type=None))
@click.option('--verbose', '-v', help='Verbose', is_flag=True)

def faf_calibration_click(spect, acgm, injected_activity, half_life, delta_time, acquisition_duration, output, verbose):
    '''
    Create a new calibrated SPECT image with the FAF method, using the ACGM planar image.\n

    - <spect_image> is the input 3D attenuation corrected, scatter corrected, reconstruction recovery SPECT, in counts\n
    - <ACGM_image>  is the registered attenuation corrected geometrical mean Image (usually the output of sydFAF_ACGM_Image)\n

    The output is a calibrated 3D SPECT in MBq/mm3. Calibration FAF factor is printed.
    
    '''

    spectImage = itk.imread(spect)
    acgmImage = itk.imread(acgm)
    outputImage, fafFactor = faf_calibration(spectImage, acgmImage, injected_activity, half_life, delta_time, acquisition_duration)
    print("Calibration FAF factor (MBq/count): " + str(fafFactor))
    itk.imwrite(outputImage, output)

# -----------------------------------------------------------------------------
def faf_calibration(spect, acgm, injected_activity=1.0, half_life=6.0067, delta_time=1.0, acquisition_duration=900, verbose=False):

    if spect.GetImageDimension() != 3:
        print("spect image dimension (" + str(spect.GetImageDimension()) + ") is not 3")
        sys.exit(1)

    if acgm.GetImageDimension() != 2:
        print("acgm image dimension (" + str(acgm.GetImageDimension()) + ") is not 2")
        sys.exit(1)

    projectedSPECT = image_projection.image_projection(spect, 1)
    flipFilter = itk.FlipImageFilter.New(Input=projectedSPECT)
    flipFilter.SetFlipAxes((False, True))
    flipFilter.Update()
    projectedSPECT = flipFilter.GetOutput()
    projectedSPECT = gt.applyTransformation(input=projectedSPECT, like=acgm, force_resample=True)
    projectedSPECTArray = itk.array_from_image(projectedSPECT)
    acgmArray = itk.array_from_image(acgm)
    spectArray = itk.array_from_image(spect)

    lambdaDecay = np.log(2.0)/(half_life*3600)
    A0 = injected_activity*np.exp(-lambdaDecay*delta_time*3600)
    #integral = (1 - np.exp(-lambdaDecay*acquisition_duration))/lambdaDecay
    #integralActivity = A0*integral
    #volume = np.prod(np.array(spect.GetSpacing()))

    sumSPECT = np.sum(spectArray)
    sumACGM = np.sum(acgmArray)
    partialSumACGM = np.sum(acgmArray[projectedSPECTArray > 1])

    sensitivityFAF = sumSPECT/(A0 * partialSumACGM/sumACGM)

    if verbose:
        print("sum in SPECT (counts): " + str(sumSPECT))
        print("partial sum in ACGM (counts): " + str(partialSumACGM))
        print("sum in ACGM (counts): " + str(sumACGM))
        print("FAF: " + str(partialSumACGM/sumACGM))
        print("A0 at the beginning of the SPECT acquisition (MBq): " + str(A0))
        print("lambda decay (s-1): " + str(lambdaDecay))
        #print("volume of SPECT (mm3): " + str(volume))
        #print("integral Activity (MBq.s): " + str(integralActivity))

    calibratedSpectArray = spectArray/sensitivityFAF
    calibratedSpectImage = itk.image_from_array(calibratedSpectArray)
    calibratedSpectImage.CopyInformation(spect)

    return (calibratedSpectImage, sensitivityFAF)

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    faf_calibration_click()

# -----------------------------------------------------------------------------
import unittest

class Test_Faf_Calibration_(unittest.TestCase):
    def test_faf_calibration(self):
        gm = np.ones((32,12))*11.2
        spect = np.ones((16,16,6))*0.33
        gmImage = itk.image_from_array(gm)
        gmImage.SetOrigin(np.array([-6.0, -16.0]))
        spectImage = itk.image_from_array(spect)
        spectImage.SetOrigin(np.array([-3.0, -8.0, -8.0]))
        calibratedSpectImage, sensitivityFAF = faf_calibration(spectImage, gmImage, 1.0, half_life=4, delta_time=4, verbose=True)
        calibratedSpectArray = itk.array_from_image(calibratedSpectImage)

        self.assertTrue(calibratedSpectImage.GetLargestPossibleRegion().GetSize()[0] == 6)
        self.assertTrue(calibratedSpectImage.GetLargestPossibleRegion().GetSize()[1] == 16)
        self.assertTrue(calibratedSpectImage.GetLargestPossibleRegion().GetSize()[2] == 16)
        theoreticalSensitivityFaf = 6*16*16*0.33/(0.5*0.25)
        self.assertTrue(np.allclose(sensitivityFAF, theoreticalSensitivityFaf))
        self.assertTrue(np.allclose(calibratedSpectArray[4,12], 0.33/theoreticalSensitivityFaf))
