#!/bin/bash

 
CONFIGPROXY_AUTH_TOKEN=697c7e87dc7fbb1c0b35226d124ed20ccc3d2fbfe3757a4e86457b5851544121
PATH=/opt/conda/bin:${PATH}

source activate hub
exec jupyterhub --config ${JUPYTERHUB_CONFFILE}