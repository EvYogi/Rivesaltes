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

from smartgrid.io.export_grafana import export_to_whisper

# Default paths
DATAPATH = '/data/raw/ares/LCV_GHI'
DOWNLOAD_PATH = '/data/raw/ares'
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


def get_ares_data_from_s3(**kwargs):
    # Files are uploaded in the /data/raw/ares directory
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(config["ares_bucket"])
    ares_key = [x.key for x in bucket.objects.filter(Prefix=config["ares_bucket_prefix"])]
    logging.info("Listing " + str(len(ares_key)) + " objects ")

    for key in ares_key:
        if key.endswith(".dat"):
            file_name = '{path}/{file_name}'.format(path=DOWNLOAD_PATH, file_name=key)
            logging.info("Processing the file " + key + " => " + file_name)
            if os.path.isfile(file_name) is False:
                logging.info("Downloading file " + key)
                bucket.download_file(key, file_name)
            else:
                logging.info("File " + file_name + " already downloaded")


def clean_column_name(col):
    if col.startswith("Unnamed"):
        return ''
    else:
        return col.replace(' ', '_').replace('/', '_')

def export_data_to_grafana(**kwargs):
    historical_data = 'CMS_EXP_Walon_Donnees_1minute.dat'
    data_path = kwargs.pop('data_path', DATAPATH)
    export_path = kwargs.pop('export_path', EXPORT_PATH)
    file_name = '{data_path}/{historical_data}'.format(data_path=data_path, historical_data=historical_data)

    #loading header
    df_header = pd.read_csv(file_name, sep=',', parse_dates=[0],
                            header=[1, 2, 3], nrows=10)
    df_header.columns = ['-'.join([clean_column_name(name) for name in col]).strip() for col in df_header.columns.values]
    logging.info("Headers loaded " + str(df_header.columns))
    
    for file_name in glob.glob(data_path + "/*.dat"):
        logging.info("Processing the file '{file_name}'".format(file_name=file_name))

        # File is not yet imported
        if os.path.isfile(file_name + ".OK") is False:
            skiprows = 0
            first_line = open(file_name).readline()
            logging.info("First line " + first_line)

            
            if first_line.startswith('"TOA5"'):
                skiprows = 4
                
            df = pd.read_csv(file_name, sep=',', parse_dates=[0], skiprows=skiprows, names=df_header.columns)
            export_to_whisper(df, export_path,
                              "ares",
                              ['1m:3y', '10m:5y', '1d:10y'],
                              timestamp_column='TIMESTAMP-TS-', overwrite=False)
            # Writing the OK file, to skip this file on the next run
            with open(file_name + ".OK", "w+") as fp:
                fp.write("DONE")
        else:
            logging.info("Skipping file '{file_name}'".format(file_name=file_name))



# DAG configuration
dag = DAG('Rivesaltes_ares_data_integration',
          description='integration of ares data',
          default_args=default_args,
          schedule_interval='0 6 * * *',
          start_date=datetime(2017, 3, 20),
          catchup=False)

get_store = PythonOperator(task_id='get_ares_data_from_s3',
                           python_callable=get_ares_data_from_s3,
                           provide_context=True, dag=dag)

export_grafana = PythonOperator(task_id='export_data_to_grafana',
                                python_callable=export_data_to_grafana,
                                provide_context=True, dag=dag,
                                export_path=EXPORT_PATH,
                                data_path=DATAPATH)


get_store >> export_grafana
