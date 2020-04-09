#!/usr/bin/env python

import click
import math
import datetime

def date2datetime(text):
    #available date format:
    #"dd/mm/yyyy hh:mm" or "hh:mm"
    if '/' in text:
        date_object = datetime.datetime.strptime(text, '%d/%m/%y %H:%M')
    else:
        date_object = datetime.datetime.strptime(text, '%H:%M')
    return date_object



CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('-r', '--radionuclide', type=str, help='Radionuclide')
@click.option('-a', '--activity', type=float, help='Injected activity')
@click.option('-i', '--injection', type=str, help='Injection date, format: "dd/mm/yyyy hh:mm" or "hh:mm"')
@click.option('-j', '--acquisition', type=str, help='Acquisition date, format: "dd/mm/yyyy hh:mm" or "hh:mm"')
@click.option('-t', '--timegap', type=str, help='Time gap betwee injection and acquisition dates, format: "dd/mm/yyyy hh:mm", "hh:mm" or "ssssssss"')

def radioactiveDecay_click(radionuclide, activity, injection, acquisition, timegap):
    """
    \b
    Compute the activity of the radionuclide at the acquisition date (or if not set, considering the gap time in day or second format)
    radionuclide:
     - Tc99m
     - Y90
     - Lu177
     - Ga68
     - In111
    """
    
    output = radioactiveDecay(radionuclide, activity, injection, acquisition, timegap)
    print("New activity: ")
    print(output)

def radioactiveDecay(radionuclide, activity, injection, acquisition, timegap):
    halftime = 1.0 #in sec
    if radionuclide == "Tc99m":
        halftime = 21624.12
    elif radionuclide == "Y90":
        halftime = 230549.76
    elif radionuclide == "Lu177":
        halftime = 574300.8
    elif radionuclide == "Ga68":
        halftime = 4069.8
    elif radionuclide == "In111":
        halftime = 242343.36

    deltaTime = 0 #in sec
    if acquisition != None and injection != None:
        deltaTime = (date2datetime(acquisition) - date2datetime(injection)).total_seconds()
    elif timegap != None:
        if ':' in timegap:
            deltaTime = (date2datetime(timegap) - date2datetime("0:0")).total_seconds()
        else:
            deltaTime = float(timegap)

    output = activity*math.exp(-deltaTime*math.log(2)/halftime)
    return output


if __name__ == '__main__':
    radioactiveDecay_click()

# -----------------------------------------------------------------------------
import unittest

class Test_Anonymize(unittest.TestCase):
    def test_anonymize(self):
        output = radioactiveDecay("Tc99m", 1, "10:00", "11:00", None)
        self.assertTrue(output == 0.89101352540955)
