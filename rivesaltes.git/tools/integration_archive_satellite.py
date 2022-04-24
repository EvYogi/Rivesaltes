# -*- coding: utf-8 -*-
# /usr/bin/env python

# This snippet of code uploads historic values saved as HDF5 files at first argument into bucket specified
# as second argument to the path /bucket/processed/YYYY/MM/DD/HHMM.jpg with a specific origin
# (visual_complete or infra_polair), specified as the third argument

# example of use python ../hdf5/file.h5 my_bucket visual polair


# Imports
import sys
import h5py
from PIL import Image
import io
import boto3


# Code
path_to_archive = sys.argv[1]
bucket = sys.argv[2]
type_image = sys.argv[3]


historic = h5py.File(path_to_archive, 'r')
s3 = boto3.client('s3')

for i in range(historic['DATA'].shape[0]):
    ima = Image.fromarray(historic['DATA'][0].transpose())
    timestamp = historic['TU'][:, i]
    key = str(timestamp[0])+'/' + str(timestamp[1]).zfill(2) + '/' + str(timestamp[2]).zfill(2)+'/' + \
          str(timestamp[3]).zfill(2) + str(timestamp[4]).zfill(2)
    with io.BytesIO() as f:
        ima.save(f, format='JPEG')
        f.seek(0)
        s3.put_object(Body=f,
                      Bucket=bucket, Key='processed/'+'image_sat_'+sys.argv[3]+'/'+key+'.jpg')
