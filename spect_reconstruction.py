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
@click.option('--rotation', type=click.Choice(['GE', 'Gate', 'None']), default='None')
@click.option('--scaling_factor', 'scaling_factor', default=10000, help='Scaling factor for the GE attenuation map')
def spect_reconstruction_click(input_image, output_image, geometry_file, attenuation_map, nb_iteration,
                               nb_subset, rotation, scaling_factor):
    '''
    Compute a reconstruction using rtk OSEM algorithm
    '''
    image = itk.imread(input_image, itk.F)
    res = spect_reconstruction(image, geometry_file, attenuation_map, int(nb_iteration), int(nb_subset),
                               rotation, float(scaling_factor))
    itk.imwrite(res, output_image)


def spect_reconstruction(image, geometry_file, attenuation_map, nb_iteration, nb_subset,
                         rotation, scaling_factor):
    att_map = itk.imread(attenuation_map, itk.F)
    if rotation == 'GE':
        matrix = np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, -1.0, 0, 0], [0, 0, 0, 1.0]], dtype=float)
        matrix = itk.matrix_from_array(matrix)
        att_map = gt.applyTransformation(input=att_map, matrix=matrix, force_resample=False)
        att_map = gt.image_divide([att_map, scaling_factor])
    elif rotation == 'Gate':
        matrix = np.array([[1.0, 0, 0, 0], [0, 0, -1.0, 0], [0, -1.0, 0, 0], [0, 0, 0, 1.0]])
        matrix = itk.matrix_from_array(matrix)
        att_map = gt.applyTransformation(input=att_map, matrix=matrix, force_resample=True)

    nb_projection = itk.array_from_image(image).shape[0]
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

    if rotation == 'GE':
        matrix_inv = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=float)
        matrix_inv = itk.matrix_from_array(matrix_inv)
        reconstruction = gt.applyTransformation(
            input=reconstruction, matrix=matrix_inv, force_resample=True)

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
        filenameImageMhd = wget.download(
            "https://gitlab.in2p3.fr/OpenSyd/syd_tests/-/raw/master/dataTest/image_corrected.mhd?inline=false",
            out=tmpdirpath, bar=None)
        filenameImageRaw = wget.download(
            "https://gitlab.in2p3.fr/OpenSyd/syd_tests/-/raw/master/dataTest/image_corrected.raw?inline=false",
            out=tmpdirpath, bar=None)
        filenameGeom = wget.download(
            "https://gitlab.in2p3.fr/OpenSyd/syd_tests/-/raw/master/dataTest/geom.xml?inline=false",
            out=tmpdirpath, bar=None)
        filenameMap = wget.download(
            "https://gitlab.in2p3.fr/OpenSyd/syd_tests/-/raw/master/dataTest/attenuation_map.dcm?inline=false",
            out=tmpdirpath, bar=None)
        filenameReconMhd = wget.download(
            "https://gitlab.in2p3.fr/OpenSyd/syd_tests/-/raw/master/dataTest/reconstruction.mhd?inline=false",
            out=tmpdirpath, bar=None)
        filenameReconRaw = wget.download(
            "https://gitlab.in2p3.fr/OpenSyd/syd_tests/-/raw/master/dataTest/reconstruction.raw?inline=false",
            out=tmpdirpath, bar=None)
        image = itk.imread(filenameImageMhd, itk.F)
        # Test reconstruction
        res = spect_reconstruction(image, filenameGeom, filenameMap, 15, 4, None, 10000)
        init_image = itk.imread(filenameReconMhd, itk.F)
        res_array = itk.array_from_image(res)
        init_array = itk.array_from_image(init_image)
        test = np.subtract(res_array, init_array, out=np.zeros_like(init_array), dtype=np.float32)
        self.assertTrue(np.count_nonzero(test) == 0)
        # Test reconstruction with rotation
        res = spect_reconstruction(image, filenameGeom, filenameMap,15,4, 'GE',10000)
        res_array = itk.array_from_image(res)
        self.assertTrue(res_array!=[])


        shutil.rmtree(tmpdirpath)
