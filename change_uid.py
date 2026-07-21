
import os
import click
import pydicom

dict_uid = {}

def changeUID(ds, tag):
  if ds[tag].value not in dict_uid.keys():
      new_uid = pydicom.uid.generate_uid()
      dict_uid[ds[tag].value] = new_uid
  ds[tag].value = str.encode(dict_uid[ds[tag].value])
  return(ds)


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('-i', '--inputfolder', default='.', help='Input folder where dicoms are present')
def change_uid_click(inputfolder):
    """
    \b
    :param inputfolder: Folder containing all dicom files to be anonymized
    :return: Dicom files with the new uid inside inputfolder/anonymizationOutput/

    eg: python ~/bin/change_uid.py -i BR^^

    change:
    (0x08, 0x18) # SOP Instance UID
    (0x20, 0x0d) # Study Instance UID
    (0x20, 0x0e) # Series Instance UID
    (0x20, 0x52) # Frame of Reference UID
    """

    change_uid(inputfolder)

def change_uid(inputfolder):

    beginningFolder = os.getcwd()
    os.chdir(inputfolder)
    outputPath = os.path.join(os.getcwd(), "anonymizationOutput")
    os.makedirs(outputPath)
    exclude = ["anonymizationOutput"]
    for root, dirs, files in os.walk('.', topdown=True):
        dirs[:] = [d for d in dirs if d not in exclude]
        for file in files:
            if not os.path.isdir(os.path.join(outputPath, root)):
                   os.makedirs(os.path.join(outputPath, root))
            try:
                ds = pydicom.read_file(os.path.join(root, file), force=True)
                ds = changeUID(ds, (0x08, 0x18)) # SOP Instance UID
                ds = changeUID(ds, (0x20, 0x0d)) # Study Instance UID
                ds = changeUID(ds, (0x20, 0x0e)) # Series Instance UID
                ds = changeUID(ds, (0x20, 0x52)) # Frame of Reference UID
                ds.save_as(os.path.join(outputPath, root, file))

            except Exception as e:
                print(e)
                if not file.endswith(".dat") and not file.endswith(".mhd") and not file.endswith(".raw") \
                   and not file.endswith(".INI") and not file.endswith(".XVI") and not file.endswith(".SCAN") \
                   and not file.endswith(".REFSCAN") and not file.endswith(".REFPATIENTORIENTATION") and not file.endswith(".REFORIENTATION") \
                   and not file.endswith(".DELINEATION") and not file.endswith(".tar.bz2") and not file.startswith("Angle.") \
                   and not file.endswith(".jpg") and not file.endswith(".his"):
                    print(os.path.join(inputfolder, root, file) + " is not a correct dicom file")
                shutil.copyfile(os.path.join(root, file), os.path.join(outputPath, root, file))

    os.chdir(beginningFolder)

if __name__ == '__main__':
    change_uid_click()



