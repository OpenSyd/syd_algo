#!/usr/bin/env python

import numpy as np
from itk import RTK as rtk


class ListModeReader:
    def __init__(self, file_name, duration_frame=None, frame=None, time_start=None):
        self.file_name = file_name
        self.duration_frame = duration_frame
        self.frame = frame
        self.motion_info = {}
        self.data = 0
        self.header = 0
        self.nb_frame = 1
        if time_start is None:
            self.time_start = 0
        else:
            self.time_start = time_start

    def read(self):
        data_npz = np.load(self.file_name)
        self.header = data_npz['header']
        motion = data_npz['motion']
        self.data = data_npz['data']
        if self.frame is not None:
            self.nb_frame = self.frame
        else:
            self.nb_frame = motion.shape[0]
        for f in range(1, self.nb_frame + 1):
            angle = float(motion['angle'][f - 1])
            ind_start = np.where(self.data['angle'] == angle)[0][0]
            start = self.data['time'][ind_start] + self.time_start
            if self.duration_frame is not None:
                stop = start + self.duration_frame - 1
            else:
                ind_stop = np.where(self.data['angle'] == angle)[0][-1]
                stop = self.data['time'][ind_stop]
            self.motion_info[f] = {'angle': angle, 'start': start, 'stop': stop,
                                   'radius_head_1': float(motion['radius_head_1'][f - 1]),
                                   'radius_head_2': float(motion['radius_head_1'][f - 1])}

    def get_rtk_geometry(self):
        geometry = rtk.ThreeDCircularProjectionGeometry.New()
        for i in sorted(self.motion_info.keys()):
            geometry.AddProjection(self.motion_info[i]['radius_head_1'], 0, self.motion_info[i]['angle'])
        for i in sorted(self.motion_info.keys()):
            geometry.AddProjection(self.motion_info[i]['radius_head_2'], 0, self.motion_info[i]['angle'] + 180)
        return geometry

    def write_xml_geometry(self, geometry_path):
        geometry = self.get_rtk_geometry()
        xmlWriter = rtk.ThreeDCircularProjectionGeometryXMLFileWriter.New()
        xmlWriter.SetFilename(geometry_path)
        xmlWriter.SetObject(geometry)
        xmlWriter.WriteFile()


