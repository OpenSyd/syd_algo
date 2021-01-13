#!/usr/bin/env python

import numpy as np
import itk
import click
import re
import os
import json
from listmode_reader import ListModeReader

def projection(x, y, weight, size_matrix, spacing, gate=False):
    p = np.zeros((size_matrix[1], size_matrix[0]))
    dec_x = 0.5 * spacing[0] * (size_matrix[0] - 1)
    dec_y = 0.5 * spacing[1] * (size_matrix[1] - 1)
    if gate:
        dec_x += 2.20903
        dec_y += 2.20903
    for k in range(len(x)):
        j = int((x[k] + dec_x) / spacing[0])
        i = int((-y[k] + dec_y) / spacing[1])
        if 0 <= i < size_matrix[1] and 0 <= j < size_matrix[0]:
            p[i, j] += weight[k]
    for i in range(size_matrix[1]):
        for j in range(size_matrix[0]):
            if p[i, j] != 0:
                p[i, j] = round(p[i, j])
    p = p.astype(int)
    return p


# -----------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--input', '-i', 'input_file', help='Input npz list mode file')
@click.option('--output', '-o', 'output_name', default='projection.mhd', help='Projections')
@click.option('--dimension', default='128', help='Dimension of the projection (default=\'128\')')
@click.option('--origin', default='', help='Origin (default=centered)')
@click.option('--spacing', default='4.41806', help='Spacing (default=\'4.41806\')')
@click.option('--direction', 'output_direction', default='', help='Direction')
@click.option('--like', default="", help='Copy information from this image (origin, dimension, spacing, direction)')
@click.option('--geometry', default='geom.xml', help='Save the geometry in a xml file')
@click.option('--frame', default='all', help='Number of frame to read in the listmode file (default=\'all\')')
@click.option('--durationframe', 'duration_frame', default='all', help='Duration of one frame in the listmode file')
@click.option('--json', '-j', 'json_file',help='JSON file path containing the lower and upper limit for the principal window and for the scatter window')
@click.option('--divideproj', 'divide_proj', default=1)
def listmode2projectionClick(input_file, output_name, dimension, origin, spacing, output_direction, like, geometry, frame,duration_frame, json_file, divide_proj):
    """
    \b
    Compute projections from json List Mode file (input_file), and save them in mhd or mha format (output_name).
    The user can choose the number of frame to read in the json list mode file (frame) and the duration of one frame (duration_frame).
    """
    listmode2projection(input_file, output_name, dimension, origin, spacing, output_direction, like, geometry, frame,duration_frame,json_file, divide_proj)


def listmode2projection(input_file, output_name, dimension, origin, spacing, output_direction, like, geometry, frame,duration_frame, json_file, divide_proj):
    """
    \b
    Compute projections from npz List Mode file (input_file), and save them in mhd or mha format (output_name).
    The user can choose the number of frame to read in the npz list mode file (frame) and the duration of one frame (duration_frame).
    """
    if frame.lower() == 'all':
        frame = None
    elif frame.isdigit():
        frame = int(frame)
    if duration_frame.lower() == 'all':
        duration_frame = None
    elif duration_frame.isdigit():
        duration_frame = int(duration_frame)

    if like == "":
        dimension = [int(s) for s in re.findall(r"[-+]?\d*\.\d+|\d+", dimension)]
        if len(dimension) == 1:
            dimension.append(dimension[0])
        spacing = [float(s) for s in re.findall(r"[-+]?\d*\.\d+|\d+", spacing)]
        if len(spacing) == 1:
            spacing.append(spacing[0])
            spacing.append(1)
        elif len(spacing) == 2:
            spacing.append(1)
        if origin == '':
            origin = [-0.5 * spacing[0] * (dimension[0] - 1), -0.5 * spacing[1] * (dimension[1] - 1), 0]
        else:
            origin = [float(s) for s in re.findall(r"[-+]?\d*\.\d+|\d+", origin)]
            if len(origin) == 1:
                origin.append(origin[0])
                origin.append(0)
            elif len(origin) == 2:
                origin.append(0)
        if output_direction == '':
            output_direction = np.eye(3)
        else:
            output_direction = [float(s) for s in re.findall(r"[-+]?\d*\.\d+|\d+", output_direction)]
            if len(output_direction) != 9:
                print(" {} invalid direction argument".format(output_direction))
                exit(0)
                output_direction = np.reshape(output_direction, (3, 3))
    else:
        pixelType = itk.F
        imageType = itk.Image[pixelType, 3]
        readerType = itk.ImageFileReader[imageType]
        reader = readerType.New()
        reader.SetFileName(like)
        reader.Update()
        origin = reader.GetOutput().GetOrigin()
        spacing = reader.GetOutput().GetSpacing()
        size = reader.GetOutput().GetLargestPossibleRegion().GetSize()
        dimension = list(size)[:2]
        output_direction = reader.GetOutput().GetDirection()

    
    with open(json_file) as j:
        data=json.load(j)

    for p in data:
        peak_principal_inf = p['peak_principal_inf']
        peak_principal_sup = p['peak_principal_sup']
        peak_scatter_inf = p['peak_scatter_inf']
        peak_scatter_sup = p['peak_scatter_sup']


    if divide_proj == 1:
        time_start_list = [0]
    else:
        time_start_list = np.linspace(0, duration_frame, divide_proj+1)[:-1]
        duration_frame = time_start_list[1]
    for cpt, time_start in enumerate(time_start_list):
        listMode = ListModeReader(input_file, duration_frame, frame, time_start)
        listMode.read()
        gate = False
        if listMode.header["generated by"] == "Gate simulations":
            gate = True
        listMode.write_xml_geometry(geometry)

        nb_frame = listMode.nb_frame
        projection_principal = {"det1": [], "det2": []}
        projection_scatter = {"det1": [], "det2": []}
        projection_corrected = {"det1": [], "det2": []}

        for current_frame in range(1, nb_frame + 1):
            print("Frame {}".format(current_frame))
            start_frame = listMode.motion_info[current_frame]["start"]
            stop_frame = listMode.motion_info[current_frame]["stop"]
            ind_time = np.where((listMode.data['time'] >= start_frame) & (listMode.data['time'] <= stop_frame))
            energy = listMode.data['energy'][ind_time]
            x = listMode.data['x'][ind_time]
            y = listMode.data['y'][ind_time]
            head = listMode.data['head'][ind_time]
            weight = listMode.data['weight'][ind_time]
            ind_principal = np.where((energy >= peak_principal_inf) & (energy <= peak_principal_sup))
            ind_scatter = np.where((energy >= peak_scatter_inf) & (energy <= peak_scatter_sup))
            x_principal = x[ind_principal]
            y_principal = y[ind_principal]
            det_principal = head[ind_principal]
            weight_principal = weight[ind_principal]
            x_scatter = x[ind_scatter]
            y_scatter = y[ind_scatter]
            det_scatter = head[ind_scatter]
            weight_scatter = weight[ind_scatter]
            for nb_det in [1, 2]:
                ind = np.where(det_principal == nb_det)
                p_principal = projection(x_principal[ind], y_principal[ind],
                                         weight_principal[ind], dimension, spacing, gate)
                projection_principal["det" + str(nb_det)].append(p_principal)
                ind = np.where(det_scatter == nb_det)
                p_scatter = projection(x_scatter[ind], y_scatter[ind],
                                       weight_scatter[ind], dimension, spacing, gate)
                projection_scatter["det" + str(nb_det)].append(p_scatter)
        
        itkimg = np.stack(projection_principal["det1"] + projection_principal["det2"] + projection_scatter["det1"] + projection_scatter["det2"])
        itkimg = itkimg * divide_proj
        itkimg = itk.GetImageFromArray(itkimg.astype(np.float32))
        itkimg.SetOrigin(origin)
        itkimg.SetSpacing(spacing)
        if isinstance(output_direction, np.ndarray):
            direction_matrix = itk.GetMatrixFromArray(output_direction)
        else:
            direction_matrix = itk.GetMatrixFromArray(itk.GetArrayFromVnlMatrix(output_direction.GetVnlMatrix().as_matrix()))
        itkimg.SetDirection(direction_matrix)
        if len(time_start_list) == 1:
            projection_path = output_name
        else:
            projection_path = os.path.splitext(output_name)
            projection_path = projection_path[0] + "_" + str(cpt) + projection_path[1]
        itk.imwrite(itkimg, projection_path)

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    listmode2projectionClick()

# -----------------------------------------------------------------------------
import unittest
import tempfile
import shutil
import os
import wget

class Test_listmode2projection_(unittest.TestCase):
    def test_listmode2projection(self):
        print('\n')
        tmpdirpath = tempfile.mkdtemp()
        filenameMhd = wget.download("https://gitlab.in2p3.fr/OpenSyd/syd_tests/-/raw/master/dataTest/fantome_sans_correction.mhd?inline=false", out=tmpdirpath, bar=None)
        filenameRaw = wget.download("https://gitlab.in2p3.fr/OpenSyd/syd_tests/-/raw/master/dataTest/fantome_sans_correction.raw?inline=false", out=tmpdirpath, bar=None)
        filenameNpz = wget.download("https://gitlab.in2p3.fr/OpenSyd/syd_tests/-/raw/master/dataTest/fantome.npz?inline=false", out=tmpdirpath, bar=None)
        filenameJson = wget.download("https://gitlab.in2p3.fr/OpenSyd/syd_tests/-/raw/master/dataTest/fantome.json?inline=false", out=tmpdirpath, bar=None)
        npz = os.path.join(tmpdirpath, filenameNpz)
        json = os.path.join(tmpdirpath, filenameJson)
        geom = os.path.join(tmpdirpath, 'geom.xml')
        output = os.path.join(tmpdirpath, 'projection.mhd')
        listmode2projection(input_file=npz, output_name=output, dimension='128', origin='', spacing='4.41806', output_direction='', like='', geometry=geom, frame='all',duration_frame='25000', json_file=json, divide_proj=1)
        mhd = itk.imread(filenameMhd)
        mhd_array = itk.array_from_image(mhd)
        res = itk.imread(output)
        res_array = itk.array_from_image(res)
        test = np.subtract(res_array,mhd_array ,out=np.zeros_like(mhd_array, dtype=np.float32))
        self.assertTrue(os.path.isfile(geom))
        self.assertTrue(os.path.isfile(output))
        self.assertTrue(np.count_nonzero(test)<=4000)
        shutil.rmtree(tmpdirpath)
