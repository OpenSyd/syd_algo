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
import faf_create_planar_geometrical_mean
import faf_register_planar_image
import faf_ACF_image
import faf_ACGM_image
import faf_calibration

# -----------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)

@click.option('--spect', '-s', help='Input SPECT image filename', required=True, type=click.Path(dir_okay=False))
@click.option('--ct', '-c', help='Input CT image filename', required=True, type=click.Path(dir_okay=False))
@click.option('--planar', '-p', help='Input planar WB image filename', required=True, type=click.Path(dir_okay=False))
@click.option('--injected_activity', '-a', help='Injected activity for the SPECT in MBq', required=True, default=1.0)
@click.option('--delta_time', '-t', help='Time between injection and beginning of the SPECT acquisition in h', required=True, default=1.0)
@click.option('--output', '-o', help='Output filename', required=True,
                type=click.Path(dir_okay=False,
                              writable=True, readable=False,
                              resolve_path=True, allow_dash=False, path_type=None))

def faf_lutetium_calibration_click(spect, ct, planar, injected_activity, delta_time, output):
    '''
    Full FAF calibration for Lutetium images \n

    - <spect_image> is the input 3D attenuation corrected, scatter corrected, reconstruction recovery SPECT, in counts\n
    - <ct_image>  is the CT Image\n
    - <planar_image>  is the Whole Body Planar Image. For Lutetium, there is 8 slices for 113keV and 208keV windows in that order: 113_ANT_primary, 113_POST_primary, 208_ANT_primary, 208_POST_primary, 113_ANT_scatter, 113_POST_scatter, 208_ANT_scatter, 208_POST_scatter\n

    The output is a calibrated 3D SPECT in MBq. Calibration sensitivity FAF factor is printed.
    
    '''

    spectImage = itk.imread(spect)
    ctImage = itk.imread(ct)
    planarImage = itk.imread(planar)
    outputImage = faf_lutetium_calibration(spectImage, ctImage, planarImage, injected_activity, delta_time)
    itk.imwrite(outputImage, output)

# -----------------------------------------------------------------------------
def faf_lutetium_calibration(spect, ct, planar, injected_activity, delta_time):

    if spect.GetImageDimension() != 3:
        print("spect image dimension (" + str(spect.GetImageDimension()) + ") is not 3")
        sys.exit(1)
    
    if ct.GetImageDimension() != 3:
        print("ct image dimension (" + str(ct.GetImageDimension()) + ") is not 3")
        sys.exit(1)

    if planar.GetImageDimension() != 3:
        print("planar image dimension (" + str(planar.GetImageDimension()) + ") is not 3")
        sys.exit(1)
    if planar.GetLargestPossibleRegion().GetSize()[2] != 8:
        print("planar image dimension (" + str(planar.GetLargestPossibleRegion().GetSize()[2]) + ") is not 8")
        sys.exit(1)

    planarArray = itk.array_from_image(planar)
    tempArray1 = planarArray[2:4,:,:]
    tempArray2 = planarArray[6:8,:,:]
    planar208Array = np.concatenate([tempArray1, tempArray2], axis=0)
    planar208Image = itk.image_from_array(planar208Array)
    planar208Image.SetSpacing(planar.GetSpacing())
    planar208Image.SetOrigin(planar.GetOrigin())
    
    gmImage = faf_create_planar_geometrical_mean.faf_create_planar_geometrical_mean(planar208Image)
    registeredGmImage = faf_register_planar_image.faf_register_planar_image(gmImage, spect)
    acfImage = faf_ACF_image.faf_ACF_image(ct, [0.2068007, 0.57384408],  [0.00014657, 0.13597229, 0.24070651])
    acgmImage = faf_ACGM_image.faf_ACGM_image(registeredGmImage, acfImage)
    calibratedSpectImage, fafFactor = faf_calibration.faf_calibration(spect, acgmImage, injected_activity, 6.647*24,delta_time, 900, True)
    print("Calibration sensitivity FAF factor (MBq/count): " + str(fafFactor))
    return calibratedSpectImage

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    faf_lutetium_calibration_click()
