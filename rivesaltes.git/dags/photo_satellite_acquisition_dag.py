# Imports
from datetime import datetime
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import numpy as np
from time import gmtime, strftime
from datetime import timedelta
import io
from PIL import Image
import boto3
import urllib
import json
import logging
import os
from airflow.operators.sensors import BaseSensorOperator
from airflow.api.common.experimental.trigger_dag import trigger_dag
from botocore.errorfactory import ClientError


from smartgrid.image_processing.satellite_image_processing import remove_borders_with_convolution

# Parameters & config
default_args = {
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
    'task_concurrency': 8,
    'depends_on_past': False
}

# Get directory of current running file
workflow_dir = os.path.dirname(os.path.abspath(__file__))
# Set working directory of Python script
os.chdir(workflow_dir)


# Logical code
def get_date_quarterly(context=None):
    """
    Generate a string of date, format YYYYMMDDHHMM with a quarter modulo
    :return: date in string
    """
    if context is not None:
        execdate = context.get("execution_date")
        logging.info("Execution date " + str(execdate))
        date = execdate.strftime("%Y%m%d%H")
        minute = execdate.minute
        quarter = minute // 15
        minute_quartered = 15 * quarter
        date = date + str(minute_quartered).zfill(2)
        logging.info("==> Query date " + date)
    else:
        globaltime = gmtime()
        date = strftime("%Y%m%d%H", globaltime)
        minute = globaltime.tm_min
        quarter = minute // 15
        minute_quartered = 15 * quarter
        date = date + str(minute_quartered).zfill(2)
        logging.info("Old generated date " + str(date))
    return date


# Tasks description
class ImageSatSensor(BaseSensorOperator):
    """
    Class extending the BaseSensorOperator to query an endpoint given by parameter url every minute for 15 minutes
    and save it to S3 bucket whenever available
    """

    def __init__(self, url, source, bucket, *args, **kwargs):
        super(BaseSensorOperator, self).__init__(*args, **kwargs)
        self.timeout = 2700
        self.poke_interval = 120
        self.url = url
        self.source = source
        self.bucket = bucket
        self.soft_fail = False

    def poke(self, context):
        s3 = boto3.client('s3')
        date = get_date_quarterly(context)
        date_formated = date[0:4] + '/' + date[4:6] + '/' + date[6:8] + '/' + date[8:]
        byte_img = urllib.request.urlopen(self.url + date).read()

        if len(byte_img) > 154:
            s3.put_object(Body=byte_img, Bucket=self.bucket,
                          Key='LCV_SATELLITE_IMAGE_24/' + self.source + '/raw/' + date_formated + ".jpg")
            logging.info('Image is available')
        else:
            logging.info('Image is not available')

        try:
            s3.head_object(
                Bucket=self.bucket,
                Key='LCV_SATELLITE_IMAGE_24/' + self.source + '/raw/' + date_formated + '.jpg')
            exists = True
        except ClientError:
            exists = False
        return exists


def process_image_from_service(bucket=None, source=None, borders=None, **kwargs):
    s3 = boto3.client('s3')
    date = get_date_quarterly(kwargs)
    date_formated = date[0:4] + '/' + date[4:6] + '/' + date[6:8] + '/' + date[8:]
    byteimg_visual = s3.get_object(Bucket=bucket,
                                   Key='LCV_SATELLITE_IMAGE_24/' + source + '/raw/' + date_formated + ".jpg")

    img_array_visual = np.array((Image.open(byteimg_visual['Body']).convert('L')))
    img_visual_refined = remove_borders_with_convolution(img_array_visual, borders)

    with io.BytesIO() as file:
        img_visual_refined.save(file, format='JPEG')
        file.seek(0)
        s3.put_object(Body=file,
                      Bucket=bucket,
                      Key='LCV_SATELLITE_IMAGE_24/' + source + '/processed/' + date_formated + ".jpg")


# DAG configuration
with open('../conf/config.json') as json_data_file:
    config = json.load(json_data_file)


dag = DAG('Rivesaltes_image_sat_acquisition',
          description='acquisition of satellite image',
          default_args=default_args,
          schedule_interval='*/15 * * * *',
          start_date=datetime(2018, 7, 20),
          catchup=False,
          max_active_runs=10)

get_visual = ImageSatSensor(url=config['image_sat_visual_complete'],
                            source='lcv_visual_images',
                            bucket=config['bucket_S3_name'],
                            task_id='check_image_visual',
                            dag=dag)

get_polar = ImageSatSensor(url=config['image_sat_infra_polair'],
                           source='infrared_images',
                           bucket=config['bucket_S3_name'],
                           task_id='check_image_polair',
                           dag=dag)

process_visual = PythonOperator(task_id='process_visual_image_from_service',
                                python_callable=process_image_from_service,
                                op_kwargs={
                                    'bucket': config['bucket_S3_name'],
                                    'source': 'lcv_visual_images',
                                    'borders': np.load('../conf/logical_VIS_Borders.npy')
                                },
                                provide_context=True,
                                dag=dag)

process_polar = PythonOperator(task_id='process_polar_image_from_service',
                               python_callable=process_image_from_service,
                               op_kwargs={
                                   'bucket': config['bucket_S3_name'],
                                   'source': 'infrared_images',
                                   'borders': np.load('../conf/logical_IR_Borders.npy')
                               },
                               provide_context=True,
                               dag=dag)


def conditionally_trigger2(**context):
    """This function decides whether or not to Trigger the remote DAG"""
    execdate = context.get("execution_date")
    logging.info("Trigger Execution date " + str(execdate))

    hour = execdate.hour
    if hour >= 7 & hour <= 18:
        return trigger_dag('compute_GHI_prediction', execution_date=execdate)


trigger_op = PythonOperator(task_id='trigger_dagrun',
                            python_callable=conditionally_trigger2,
                            provide_context=True, dag=dag)


get_visual >> process_visual >> trigger_op
get_polar >> process_polar >> trigger_op


