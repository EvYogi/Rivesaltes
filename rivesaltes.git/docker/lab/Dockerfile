FROM 969076149354.dkr.ecr.eu-west-1.amazonaws.com/dd/lab:latest
SHELL ["/bin/bash", "-c"]

USER root
RUN apt update && apt install -y make
# FIXME: migration to ddinstall
COPY docker/lab/jupyterhub.py /etc/jupyterhub/conf

USER ddadmin
WORKDIR /opt/datadriver/workspace

COPY --chown=ddadmin:datadriver requirements.txt ./
COPY --chown=ddadmin:datadriver conda_requirements.txt ./
COPY --chown=ddadmin:datadriver Makefile ./

RUN make conda_install
RUN make pip_install

RUN source activate datadriver && \
    python -m ipykernel install --user --name datadriver --display-name "datadriver"

USER root

RUN source /opt/conda/bin/activate hub && conda install -y -c conda-forge jupyter_contrib_nbextensions jupyter_nbextensions_configurator
RUN source /opt/conda/bin/activate hub && jupyter nbextension enable collapsible_headings/main
RUN source /opt/conda/bin/activate hub && jupyter nbextension enable hide_input/main
RUN source /opt/conda/bin/activate hub && jupyter nbextension enable init_cell/main
