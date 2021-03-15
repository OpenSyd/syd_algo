#!/usr/bin/env python3

import click
import itk
from itk import RTK as rtk
import gatetools as gt
import numpy as np

# ------------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--input', '-i', 'input_image', help='Input mhd projection file')
@click.option('--output', '-o', 'output_image', help='Output mhd of the reconstructed image')
@click.option('--geom', 'geometry_file', help='Geometry file')
@click.option('--map', 'attenuation_map', help='Attenuation map file')
@click.option('--it', 'nb_iteration', help='Number of iterations for the OSEM algorithm')
@click.option('--sub', 'nb_subset', help='Number of dimensions for the OSEM algorithm')
@click.option('--proj', 'nb_projection', help='Number of projection')
@click.option('--rotation', type=click.Choice(['GE', 'Gate', 'None']), default='None')
@click.option('--scaling_factor','scaling_factor',help='Scaling factor for the GE attenuation map')
def spect_reconstruction_click(input_image, output_image, geometry_file, attenuation_map, nb_iteration,
                               nb_subset, nb_projection, rotation,scaling_factor):
    '''
    Compute a reconstruction using rtk OSEM algorithm
    '''
    image = itk.imread(input_image, itk.F)
    res = spect_reconstruction(image, geometry_file, attenuation_map, int(nb_iteration), int(nb_subset),
                               int(nb_projection), rotation,float(scaling_factor))
    itk.imwrite(res, output_image)


def spect_reconstruction(image, geometry_file, attenuation_map, nb_iteration, nb_subset, nb_projection,
                         rotation,scaling_factor):
    att_map = itk.imread(attenuation_map, itk.F)
    if rotation == 'GE':
        matrix = [[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, -1.0, 0, 0], [0, 0, 0, 1.0]]
        matrix = itk.matrix_from_array(np.array(matrix))
        att_map = gt.applyTransformation(input=att_map, matrix=matrix, force_resample=True)
        att_map = gt.image_divide([att_map, scaling_factor])
    elif rotation == 'Gate':
        matrix = [[1.0, 0, 0, 0], [0, 0, -1.0, 0], [0, -1.0, 0, 0], [0, 0, 0, 1.0]]
        matrix = itk.matrix_from_array(np.array(matrix))
        att_map = gt.applyTransformation(input=att_map, matrix=matrix, force_resample=True)

    geometryReader = rtk.ThreeDCircularProjectionGeometryXMLFileReader.New()
    geometryReader.SetFilename(geometry_file)
    geometryReader.GenerateOutputInformation()
    geometry = geometryReader.GetOutputObject()
    Dimension = 3
    pixelType = itk.F
    CPUImageType = itk.Image[pixelType, Dimension]
    OSEMType = rtk.OSEMConeBeamReconstructionFilter[CPUImageType, CPUImageType]
    imageReference = itk.imread(attenuation_map)
    volume_source = rtk.ConstantImageSource[CPUImageType].New()
    volume_source.SetInformationFromImage(imageReference)
    volume_source.SetConstant(1.)
    volume_source.Update()

    osem = OSEMType.New()
    osem.SetInput(0, volume_source)
    osem.SetInput(1, image)
    osem.SetInput(2, att_map)
    osem.SetNumberOfIterations(nb_iteration)
    osem.SetNumberOfProjectionsPerSubset(int(nb_projection / nb_subset))
    osem.SetBackProjectionFilter(6)
    osem.SetForwardProjectionFilter(4)
    osem.SetGeometry(geometry)
    osem.Update()
    reconstruction = osem.GetOutput()

    if rotation =='GE':
        matrix_inv =[[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]
        matrix_inv = itk.matrix_from_array(np.array(matrix_inv))
        reconstruction = gt.applyTransformation(
                input=reconstruction,matrix=matrix_inv,force_resample=True)


    return reconstruction


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    spect_reconstruction_click()

# -----------------------------------------------------------------------------
import unittest
import tempfile
import shutil
import os
import wget


class Test_spect_reconstruction_(unittest.TestCase):
    def test_spect_reconstruction(self):
        tmpdirpath = tempfile.mkdtemp()
        filenameMhd = wget.download(
            "https://gitlab.in2p3.fr/OpenSyd/syd_tests/-/raw/master/dataTest/image_sans_correction.mhd?inline=false",
            out=tmpdirpath, bar=None)
        filenameRaw = wget.download(
            "https://gitlab.in2p3.fr/OpenSyd/syd_tests/-/raw/master/dataTest/image_sans_correction.raw?inline=false",
            out=tmpdirpath, bar=None)
        image = itk.imread(filenameMhd)
        array = itk.array_from_image(image)
        res = spect_reconstruction(image,)
        tmpimpath = os.path.join(tmpdirpath, 'res.mhd')
        itk.imwrite(res, tmpimpath)
        im = itk.imread(tmpimpath)
        res_array = (itk.array_from_image(res)).astype(float)

        shutil.rmtree(tmpdirpath)
