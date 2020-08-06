#!/usr/bin/env python

import pydicom
import sys
import os
import click
import shutil
from encryptId import *

def anonymizeDicomFile(inputFile, outputFile, patientname, patientid):
  ds = pydicom.read_file(inputFile)
  if (0x8, 0x50) in ds:  # If Accession Number is present
    ds[(0x8, 0x50)].value = b"000000"
  if (0x8, 0x80) in ds:  # If Institution Name is present
    ds[(0x8, 0x80)].value = b"anonymous"
  if (0x8, 0x81) in ds:  # If Institution Address is present
    ds[(0x8, 0x81)].value = b"anonymous"
  if (0x8, 0x90) in ds:  # If Referring Physician's Name is present
    ds[(0x8, 0x90)].value = b"anonymous"
  if (0x8, 0x1030) in ds:  # If Study Description is present
    ds[(0x8, 0x1030)].value = b"000000"
  if (0x8, 0x1040) in ds:  # If Department Name is present
    ds[(0x8, 0x1040)].value = b"anonymous"
  if (0x8, 0x1048) in ds:  # If Physician(s) of Record is present
    ds[(0x8, 0x1048)].value = b"anonymous"
  if (0x8, 0x1060) in ds:  # If Name of Physician(s) Reading Study is present
    ds[(0x8, 0x1060)].value = b"anonymous"
  if (0x8, 0x1070) in ds:  # If Referring Operators' Name is present
    ds[(0x8, 0x1070)].value = b"anonymous"
  if (0x9, 0x1040) in ds:  # If Patient Object Name is present
    ds[(0x9, 0x1040)].value = b"anonymous"
  if (0x9, 0x1042) in ds:  # If Patient Creation Date is present
    ds[(0x9, 0x1042)].value = b"000000"
  if (0x9, 0x1043) in ds:  # If Patient Creation Time is present
    ds[(0x9, 0x1043)].value = b"000000"
  if (0x10, 0x10) in ds:  # If PatientName is present
    ds[(0x10, 0x10)].value = str.encode(patientname)
  if (0x10, 0x20) in ds:  # If Patient ID is present
    ds[(0x10, 0x20)].value = str.encode(patientid)
  if (0x10, 0x21) in ds:  # If Issuer of Patient ID is present
    ds[(0x10, 0x21)].value = b"anonymous"
  if (0x10, 0x30) in ds:  # If Patient's Birth Date is present
    ds[(0x10, 0x30)].value = b"000000"
  if (0x10, 0x40) in ds:  # If Patient's Sex is present
    ds[(0x10, 0x40)].value = b"U"
  if (0x10, 0x1000) in ds:  # If Other Patient IDs is present
    ds[(0x10, 0x1000)].value = b"000000"
  if (0x10, 0x1001) in ds:  # If Other Patient Names is present
    ds[(0x10, 0x1001)].value = b"000000"
  if (0x10, 0x1040) in ds:  # If Patient's Address is present
    ds[(0x10, 0x1040)].value = b"anonymous"
  if (0x10, 0x2160) in ds:  # If Ethnic Group is present
    ds[(0x10, 0x2160)].value = b"000000"
  if (0x10, 0x2180) in ds:  # If Occupation is present
    ds[(0x10, 0x2180)].value = b"000000"
  if (0x18, 0x1030) in ds:  # If Protocol Name is present
    ds[(0x18, 0x1030)].value = b"000000"
  if (0x20, 0x10) in ds:  # If Study Id is present
    ds[(0x20, 0x10)].value = b"000000"
  if (0x32, 0x1032) in ds: # If Requesting Physician is present
    ds[(0x32, 0x1032)].value = b"000000"
  if (0xe1, 0x1061) in ds:  # If Protocol File Name is present
    ds[(0xe1, 0x1061)].value = b"anonymous"
  if (0xe1, 0x1063) in ds:  # If Patient Language is present
    ds[(0xe1, 0x1063)].value = b"anonymous"
  ds.save_as(outputFile)


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('-i', '--inputfolder', default='.', help='Input folder where dicoms to anonymize are present')
@click.option('-f', '--force', is_flag=True, help='Force to remove output folder if present')
@click.option('-p', '--patientname', default="anonymous", help='New patient name')
@click.option('-id', '--patientid', default="000000", help='New patient id')
@click.option('-e', '--encrypt', is_flag=True, help='Encrypt patient id')
def anonymizeDicom_click(inputfolder, force, patientname, patientid, encrypt):
    """
    \b
    :param inputfolder: Folder containing all dicom files to be anonymized
    :return: Anonymized dicom inside inputfolder/anonymizationOutput/

    eg: python ~/bin/anonymize.py -i BR^^ -p "BR^^" -id 7969173 -f

    The algorithm changes these tags:\n
      (0x8, 0x50) Accession Number\n
      (0x8, 0x80) Institution Name\n
      (0x8, 0x81) Institution Address\n
      (0x8, 0x90) Referring Physician's Name\n
      (0x8, 0x1030) Study Description\n
      (0x8, 0x1040) Department Name\n
      (0x8, 0x1048) Physician(s) of Record\n
      (0x8, 0x1060) Name of Physician(s) Reading Study\n
      (0x8, 0x1070) Referring Operators' Name\n
      (0x9, 0x1040) Patient Object Name\n
      (0x9, 0x1042) Patient Creation Date\n
      (0x9, 0x1043) Patient Creation Time\n
      (0x10, 0x10) PatientName\n
      (0x10, 0x20) Patient ID\n
      (0x10, 0x21) Issuer of Patient ID\n
      (0x10, 0x30) Patient's Birth Date\n
      (0x10, 0x40) Patient's Sex\n
      (0x10, 0x1000) Other Patient IDs\n
      (0x10, 0x1001) Other Patient Names\n
      (0x10, 0x1040) Patient's Address\n
      (0x10, 0x2160) Ethnic Group\n
      (0x10, 0x2180) Occupation\n
      (0x18, 0x1030) Protocol Name\n
      (0x20, 0x10) Study Id\n
      (0x32, 0x1032) Requesting Physician\n
      (0xe1, 0x1061) Protocol File Name\n
      (0xe1, 0x1063) Patient Language\n

    Encrypt option allows you to encrypt the patient id. Be sure to have encryptId function in your python path. If encrypt is set, patientid is not taken into account.
    """

    anonymizeDicom(inputfolder, force, patientname, patientid, encrypt)

def anonymizeDicom(inputfolder, force, patientname, patientid, encrypt=False):

    os.chdir(inputfolder)
    outputPath = os.path.join(os.getcwd(), "anonymizationOutput")
    if force and os.path.isdir(outputPath):
        shutil.rmtree(outputPath)
    os.makedirs(outputPath)
    exclude = ["anonymizationOutput"]

    for root, dirs, files in os.walk('.', topdown=True):
        dirs[:] = [d for d in dirs if d not in exclude]
        for file in files:
            if not os.path.isdir(os.path.join(outputPath, root)):
                   os.makedirs(os.path.join(outputPath, root))
            try:
                ds = pydicom.read_file(os.path.join(root, file))
                realPatientId = patientid
                if (0x10, 0x20) in ds:  # If Patient ID is present
                  realPatientId = str(encryptId(int(ds[(0x10, 0x20)].value)))
                anonymizeDicomFile(os.path.join(root, file), os.path.join(outputPath, root, file), patientname, realPatientId)
            except Exception as e:
                #print(e)
                if not file.endswith(".dat") and not file.endswith(".mhd") and not file.endswith(".raw"):
                    print(os.path.join(inputfolder, root, file) + " is not a correct dicom file")
                shutil.copyfile(os.path.join(root, file), os.path.join(outputPath, root, file))

    os.chdir("..")

if __name__ == '__main__':
    anonymizeDicom_click()


# -----------------------------------------------------------------------------
import unittest
import hashlib
import wget
import tempfile

class Test_Anonymize(unittest.TestCase):
    def test_anonymize(self):
        prevdir = os.getcwd()
        tmpdirpath = tempfile.mkdtemp()
        os.chdir(tmpdirpath)
        wget.download('https://gitlab.in2p3.fr/OpenSyd/syd_tests/-/raw/master/dataTest/1.2.840.113619.2.281.3562.19216820010.1547461877.50454600.dcm')
        anonymizeDicom(".", False, "testAnonymisation", "1234567")
        with open(os.path.join(tmpdirpath, "anonymizationOutput", "1.2.840.113619.2.281.3562.19216820010.1547461877.50454600.dcm"),"rb") as fnew:
            bytesNew = fnew.read()
            new_hash = hashlib.sha256(bytesNew).hexdigest()
            self.assertTrue("b519eba34907eca4ad184a47b5a3e0ff02efdfbfa5ce1074d2ab07f91f8f6840" == new_hash)
        os.chdir(prevdir)
        shutil.rmtree(tmpdirpath)
