import os;

c = get_config()

runtime_dir = os.path.join('/srv/jupyterhub')
if not os.path.exists(runtime_dir):
    os.makedirs(runtime_dir)

hub_home = os.getenv('JUPYTERHUB_HOME')
log_file = os.getenv('JUPYTERHUB_LOG_FILE')
dd_home = os.getenv('DD_HOME')
airflow_home = os.getenv('AIRFLOW__CORE__HOME')
hub_db_file = os.getenv('JUPYTERHUB_DB_FILE')
jupyterhub_ssl_dir = os.getenv('JUPYTERHUB_SSL_DIR')


c.JupyterHub.extra_log_file = log_file
c.JupyterHub.logo_file = '{}/static/logo.png'.format(dd_home)
c.Spawner.notebook_dir = '~/'

c.JupyterHub.db_url = '{}'.format(hub_db_file)
c.JupyterHub.authenticator_class = 'jupyterhub.auth.PAMAuthenticator'
c.JupyterHub.generate_config = False
c.JupyterHub.port = 8000
#c.JupyterHub.ssl_cert = '{}/jupyterhub.crt'.format(jupyterhub_ssl_dir)
#c.JupyterHub.ssl_key = '{}/jupyterhub.key'.format(jupyterhub_ssl_dir)
#c.Spawner.default_url = '/lab'

#c.Spawner.env_keep = ['DD_HOME', 'AIRFLOW__CORE__DAGS_FOLDER', 'AIRFLOW__CORE__HOME', 'PATH', 'PYTHONPATH',
#                      'CONDA_ROOT', 'CONDA_DEFAULT_ENV', 'VIRTUAL_ENV', 'LANG', 'LC_ALL', 'AIRFLOW_HOME',
#                      'AIRFLOW__CORE__SQL_ALCHEMY_CONN']
for var in os.environ:
    c.Spawner.env_keep.append(var)

c.JupyterHub.admin_access = True
c.Authenticator.admin_users = set(["datadriver", "ddadmin"])
#c.JupyterHub.spawner_class = 'sudospawner.SudoSpawner'
#c.SudoSpawner.sudospawner_path = os.path.join(os.getenv('CONDA_PREFIX'), 'bin', 'sudospawner')
c.PAMAuthenticator.open_sessions = False
