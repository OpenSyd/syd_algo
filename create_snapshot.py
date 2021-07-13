#!/usr/bin/env python3

import SimpleITK as sitk
import matplotlib.pyplot as plt


def myshow(img, title=None, margin=0.05, dpi=80, invertX=False, invertY=False, zoom=1, save="", figsize=(0, 0)):
    nda = sitk.GetArrayFromImage(img)
    spacing = img.GetSpacing()

    if nda.ndim == 3:
        # fastest dim, either component or x
        c = nda.shape[-1]

        # the the number of components is 3 or 4 consider it an RGB image
        if c not in (3, 4):
            nda = nda[nda.shape[0] // 2, :, :]

    elif nda.ndim == 4:
        c = nda.shape[-1]

        if c not in (3, 4):
            raise RuntimeError("Unable to show 3D-vector Image")

        # take a z-slice
        nda = nda[nda.shape[0] // 2, :, :, :]

    xsize = nda.shape[1]
    ysize = nda.shape[0]

    # Make a figure big enough to accommodate an axis of xpixels by ypixels
    # as well as the ticklabels, etc...
    if figsize == (0, 0):
        figsize = (1 + margin) * xsize * zoom / dpi, (1 + margin) * ysize * zoom / dpi

    #    print(figsize)

    plt.figure(figsize=figsize, dpi=dpi, tight_layout=True)
    ax = plt.gca()

    extent = (0, xsize * spacing[0], ysize * spacing[1], 0)

    #    t = ax.imshow(nda, extent=extent, interpolation=None)
    t = ax.imshow(nda, extent=extent, interpolation=None, origin='lower')

    if invertX:
        #        print(ax.get_xlim())
        ax.set_xlim(ax.get_xlim()[1], ax.get_xlim()[0])
    if invertY:
        #        print(ax.get_ylim())
        ax.set_ylim(ax.get_ylim()[1], ax.get_ylim()[0])

    if nda.ndim == 2:
        t.set_cmap("gray")

    if (title):
        plt.title(title)

    plt.axis('off')

    if save != "":
        plt.savefig(save)
    else:
        plt.show()


def create_snapshot(ct, roi, patient, struct_name, names, id, contour):
    image_ct = sitk.ReadImage(ct)
    image_roi = sitk.ReadImage(roi)

    ### Resample roi image with CT ###
    identity = sitk.Transform(3, sitk.sitkIdentity)
    image_roi_resampled = sitk.Resample(image_roi, image_ct.GetSize(), identity, sitk.sitkNearestNeighbor,
                                        image_ct.GetOrigin(), image_ct.GetSpacing(), image_ct.GetDirection())

    ### get center of the segmentation (in physical space, then in image indices)
    statistics_label_filter = sitk.LabelShapeStatisticsImageFilter()
    statistics_label_filter.Execute(image_roi_resampled)
    centroid = statistics_label_filter.GetCentroid(1)

    centroid_indices = list(centroid)

    for i in range(0, 3):
        centroid_indices[i] = int((centroid[i] - image_ct.GetOrigin()[i]) / image_ct.GetSpacing()[i])

    ## cast CT image to char
    image_CT_256 = sitk.Cast(sitk.IntensityWindowing(image_ct, windowMinimum=20 - 700, windowMaximum=20 + 200),
                             sitk.sitkUInt8)

    if contour:
        seg = sitk.Cast(image_roi_resampled, sitk.sitkLabelUInt8)
        overlay_img = sitk.LabelMapContourOverlay(seg, image_CT_256, opacity=0.5,
                                                  contourThickness=[1, 1, 1]
                                                  )
    else:
        overlay_img = sitk.LabelOverlay(image_CT_256, image_roi_resampled, opacity=0.35)

    img_xslices = overlay_img[centroid_indices[0], :, :]
    img_yslices = overlay_img[:, centroid_indices[1], :]
    img_zslices = overlay_img[:, :, centroid_indices[2]]

    myshow(img_xslices, title=patient + " " + struct_name + " " + id, invertX=True, zoom=2.5, save=names[0],
           figsize=(7, 7))
    myshow(img_yslices, title=patient + " " + struct_name + " " + id, invertX=False, zoom=2.5, save=names[1],
           figsize=(7, 7))
    myshow(img_zslices, title=patient + " " + struct_name + " " + id, invertY=True, zoom=2.5, save=names[2],
           figsize=(7, 7))

    plt.close("all")
    return names
