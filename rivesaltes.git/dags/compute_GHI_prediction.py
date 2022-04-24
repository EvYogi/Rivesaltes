# Imports
import logging
from datetime import datetime
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import numpy as np
from datetime import timedelta
from PIL import Image
import boto3
import json
import pandas as pd
import pickle
import smartgrid
from smartgrid.image_processing.compute_GHI import predict_GHI

# Parameters & config
default_args = {
    'retries': 10,
    'retry_delay': timedelta(minutes=1)
}

with open('%s/../conf/config.json' % smartgrid.__path__[0]) as json_data_file:
    config = json.load(json_data_file)

clf = pickle.load(open('%s/../data/models/RF.pickle' % smartgrid.__path__[0], 'rb'))
clf15 = pickle.load(open('%s/../data/models/RF_15.pickle' % smartgrid.__path__[0], 'rb'))
clf60 = pickle.load(open('%s/../data/models/RF_60.pickle' % smartgrid.__path__[0], 'rb'))


# Logical code
def get_date_quarterly(date, delta):
    """
    Generate a string of date, format YYYYMMDDHHMM with a quarter modulo - delta minutes
    :return: date in string
    """
    date = date - timedelta(minutes=delta)
    minute = date.minute
    date = date.strftime("%Y%m%d%H")
    quarter = minute // 15
    minute_quartered = 15 * quarter
    date = date + str(minute_quartered).zfill(2)
    return date

# Tasks description


def process_image_prediction(**kwargs):
    datenow = kwargs.get("execution_date")
    logging.info("Execution date " + str(datenow))
 
    date = get_date_quarterly(datenow, 0)
    date_15 = get_date_quarterly(datenow, 15)

    date_formated = date[0:4]+'/'+date[4:6]+'/'+date[6:8]+'/'+date[8:]
    date_formated_15 = date_15[0:4]+'/'+date_15[4:6]+'/'+date_15[6:8]+'/'+date_15[8:]
    date_formated_ck = 'month_' + date[4:6] + '_hour_' + date[8:]

    s3 = boto3.client('s3')

    img_infrared = s3.get_object(Bucket=config['bucket_S3_name'],
                         Key='LCV_SATELLITE_IMAGE_24/infrared_images/processed/' + date_formated + ".jpg")
    img_infrared_15 = s3.get_object(Bucket=config['bucket_S3_name'],
                         Key='LCV_SATELLITE_IMAGE_24/infrared_images/processed/' + date_formated_15 + ".jpg")
    img_visual = s3.get_object(Bucket=config['bucket_S3_name'],
                         Key='LCV_SATELLITE_IMAGE_24/lcv_visual_images/processed/' + date_formated + ".jpg")

    clearsky = s3.get_object(Bucket=config['bucket_S3_name'],
                             Key='LCV_SATELLITE_IMAGE_24/clearsky_ref/' + date_formated_ck + ".jpg")
    overcast = s3.get_object(Bucket=config['bucket_S3_name'],
                             Key='LCV_SATELLITE_IMAGE_24/overcast_ref/' + date_formated_ck + ".jpg")

    img_infrared = np.array(Image.open(img_infrared['Body']).convert("L"))
    img_infrared_15 = np.array(Image.open(img_infrared_15['Body']).convert("L"))
    img_visual = np.array(Image.open(img_visual['Body']).convert("L"))
    clearsky = np.array(Image.open(clearsky['Body']))
    overcast = np.array(Image.open(overcast['Body']))
    timestamp = pd.to_datetime(date)

    results, data_point = predict_GHI(img_infrared, img_infrared_15, img_visual,
                          timestamp, clearsky, overcast, clf, clf15, clf60)

    kwargs['ti'].xcom_push(key='predictions', value=results)
    kwargs['ti'].xcom_push(key='data_point', value=data_point)


def store_results(**kwargs):
    ti = kwargs['ti']
    predictions = ti.xcom_pull(task_ids='process_image_prediction', key='predictions')
    data_point = ti.xcom_pull(task_ids='process_image_prediction', key='data_point')
    datenow = kwargs.get('execution_date')
    datenow = get_date_quarterly(datenow, 0)
    date_formated = datenow[0:4]+'/'+datenow[4:6]+'/'+datenow[6:8]+'/'+datenow[8:]

    predictions = [str(x) for x in predictions]
    pred_formated = ','.join(predictions)
    data_point = [str(x) for x in data_point]
    data_formated = ','.join(data_point)

    s3 = boto3.client('s3')
    s3.put_object(Body=pred_formated,
                  Bucket=config['bucket_S3_name'],
                  Key='LCV_GHI/predictions/' + date_formated + ".csv")
    s3.put_object(Body=data_formated, Bucket=config['bucket_S3_name'],
                  Key='LCV_GHI/data_input/' + date_formated + ".csv")


# DAG configuration
dag = DAG('compute_GHI_prediction',
          description='computation of GHI prediction from processed images',
          default_args=default_args,
          schedule_interval=None,
          start_date=datetime(2017, 3, 20),
          catchup=False)


process = PythonOperator(task_id='process_image_prediction',
                         python_callable=process_image_prediction,
                         provide_context=True, dag=dag)

store = PythonOperator(task_id='store_results',
                       python_callable=store_results,
                       provide_context=True, dag=dag)

process >> store
