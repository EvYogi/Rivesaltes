FROM 969076149354.dkr.ecr.eu-west-1.amazonaws.com/dd/factory:latest
SHELL ["/bin/bash", "-c"]

USER root
RUN apt update && apt install -y make

WORKDIR /opt/datadriver/workspace

COPY conf/ ./conf/
COPY smartgrid/ ./smartgrid/
COPY dags/ ./dags/
COPY requirements.txt ./
COPY conda_requirements.txt ./
COPY Makefile ./
COPY .airflowignore .
COPY airflow/ ./airflow/

#RUN chown -R ddadmin:datadriver /opt/datadriver/workspace/

USER ddadmin

RUN make conda_install
RUN make pip_install

USER root
RUN source activate datadriver && \
    python -m ipykernel install --user --name datadriver --display-name "datadriver"

USER ddadmin
RUN source activate datadriver && \
    python -m ipykernel install --user --name datadriver --display-name "datadriver"

#RUN source activate datadriver && conda install -y matplotlib nbconvert

