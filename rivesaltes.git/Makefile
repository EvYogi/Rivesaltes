SHELL=/bin/bash
EXEC=all
VERSION=0
DAG_FOLDER=airflow

all: 		install test nbconvert deploy purge

all_notest: 	install nbconvert deploy purge

conda_install: 	conda_requirements.txt
		source activate datadriver && conda install -c conda-forge --yes --file conda_requirements.txt

pip_install: 	requirements.txt
		source activate datadriver && pip install -r requirements.txt

install: 	conda_install pip_install

acceptance_test:	./acceptance_tests/launch_acceptance_tests.py
			source activate datadriver && \
			PYTHONPATH=PYTHONPATH:$(CURDIR) PROJECT_HOME=$(CURDIR) python ./acceptance_tests/launch_acceptance_tests.py

unittest: 
		source activate datadriver && PYTHONPATH=. PROJECT_HOME=$(CURDIR) py.test

test: 		unittest acceptance_test

deploy:
		cp -f dags/* airflow/
