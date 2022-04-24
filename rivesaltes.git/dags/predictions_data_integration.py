# Imports
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import timedelta
from datetime import datetime
import json
import glob
import logging
import os.path
import pandas as pd
import boto3
import fnmatch
import os

from smartgrid.io.export_grafana import export_to_whisper, mkdir_p

# Default paths
DATAPATH = '/data/processed/predictions'
EXPORT_PATH = '/data/datadriver_data/whisper/'

# Parameters & config
default_args = {
    'retries': 10,
    'retry_delay': timedelta(minutes=1)
}

# Try with relative path
try:
    with open('conf/config.json') as json_data_file:
        config = json.load(json_data_file)
except IOError:
    with open('/opt/datadriver/workspace/conf/config.json') as json_data_file:
        config = json.load(json_data_file)


def get_predictions_data_from_s3(**kwargs):
    # Files are uploaded in the /data/raw/ares directory
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(config["predictions_bucket"])
    predictions_key = [x.key for x in bucket.objects.filter(Prefix=config["predictions_bucket_prefix"])]
    logging.info("Listing " + str(len(predictions_key)) + " objects ")
    for key in predictions_key:
        if key.endswith(".csv"):
            file_name = '{path}/{file_name}'.format(path=DATAPATH, file_name=key)
            logging.info("Processing the file " + key + " => " + file_name)
            mkdir_p('/'.join(file_name.split('/')[:-1]))
            if os.path.isfile(file_name) is False:
                logging.info("Downloading file " + key)
                bucket.download_file(key, file_name)
            else:
                logging.info("File " + file_name + " already downloaded")


def export_data_to_grafana(**kwargs):
    data_path = kwargs.pop('data_path', DATAPATH)
    export_path = kwargs.pop('export_path', EXPORT_PATH)

    tms = []
    matches = []
    dfs = []
    for root, dirnames, filenames in os.walk(data_path):
        for filename in fnmatch.filter(filenames, '*.csv'):
            fname = filename.replace('.csv', '')
            tm = '-'.join(root.split('/')[-3:]) + " " + fname[:2] + ":" + fname[2:] + ":00"
            matches.append(os.path.join(root, filename))
            tms.append(tm)
            dfs.append(pd.read_csv(matches[-1], names=['t0', 't15', 't60']))

    df = pd.concat(dfs)
    df["tm"] = pd.to_datetime(tms)
    df = df.dropna()
    print(df)
    export_to_whisper(df, export_path,
                              "ghi",
                              ['15m:3y', '1h:5y', '1d:10y'],
                              timestamp_column='tm', overwrite=False)

# DAG configuration
dag = DAG('Rivesaltes_predictions_data_integration',
          description='integration of GHI prediction data',
          default_args=default_args,
          schedule_interval='*/15 * * * *',
          start_date=datetime(2017, 3, 20),
          catchup=False)

get_store = PythonOperator(task_id='get_predictions_data_from_s3',
                           python_callable=get_predictions_data_from_s3,
                           provide_context=True, dag=dag)

export_grafana = PythonOperator(task_id='export_data_to_grafana',
                                python_callable=export_data_to_grafana,
                                provide_context=True, dag=dag,
                                export_path=EXPORT_PATH,
                                data_path=DATAPATH)


get_store >> export_grafana
