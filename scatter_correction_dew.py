#!/usr/bin/env python

import numpy as np
import click
import itk

# -----------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(help_options=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--input','-i', 'input_file', help='Input mhd projection file')
@click.option('--output','-o','output_file',help='Output mhd file with scatter corrected projection')
@click.option('--pw','primary_window', nargs=2, type=float, help='Lower and upper limits for the primary window')
@click.option('--sw','scatter_window', nargs=2, type=float, help='Lower and upper limits for the scatter window')

def scatter_correction_dewClick(input_file, output_file, primary_window, scatter_window):
    '''
    Compute the scatter correction in a cas of a double energy window for mhd projection and save the result in a mhd file. The user need to specify the energy limits for the main window and for the scatter window.
    '''
    scatter_correction_dew(input_file, output_file, primary_window, scatter_window)

def scatter_correction_dew(input_file, output_file, primary_window, scatter_window):
    if primary_window[0] > primary_window[1]:
        primary_window = (primary_window[1], primary_window[0])
    if scatter_window[0] > scatter_window[1]:
        scatter_window = (scatter_window[1], scatter_window[0])

    projection = itk.imread(input_file)
    np_projection = (itk.array_from_image(projection)).astype(float)
    ind_principal = np.where((np_projection >= primary_window[0]) & (np_projection <= primary_window[1]))
    ind_scatter = np_where((np_projection >= scatter_window[0]) & (np_projection <= scatter_window[1]))
    p_principal = projection[ind_principal]
    p_scatter = projection[ind_scatter]
    k = 1.1
    p_corrected = np.substract(p_principal, k*p_scatter, out=np.zeros_like(p_principal dtype=np.float32), where=p_principal>k*scatter_window)
    im_corrected = itk.image_from_array(p_corrected)
    itk.imwrite(im_corrected, output_file)

# -----------------------------------------------------------------------------
if __name__=='main':
    scatter_correction_dewClick()
