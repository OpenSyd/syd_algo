
## Helpfull codes for syd and nuclear medecine images

| File                                    | Description                                                        |
| --------------------------------------- | ------------------------------------------------------------------ |
| `anonymyze.py`                          | Anonymize dicom files inside a folder                              |
| `image_projection.py`                   | Project (Sum) an image along an axis                               |
| `radioactiveDecay.py`                   | Compute radioactive activity after time delay                      |
| `stitch_image.py`                       | Stitch 2 FOV together                                              |

## FAF

| File                                    | Description                                                        |
| --------------------------------------- | ------------------------------------------------------------------ |
| `faf_create_planar_geometrical_mean.py` | 1st step: Create the geometrical mean (GM) of WB planar imag       |
| `faf_register_planar_image.py`          | 2nd step: Register the GM with the SPECT image                     |
| `faf_ACF_image.py`                      | 3rd step: Convert CT to Attenuation Correction Factor image        |
| `faf_ACGM_image.py`                     | 4th step: Compute the Attenuation Corrected GM image               |
| `faf_calibration.py`                    | 5th step: Calibrate the SPECT to have MBq                          |
| `faf_lutetium_calibration.py`           | All-in-one step for Lutetium                                       |

