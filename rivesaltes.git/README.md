# Install 

create a conda environment with the command
```
conda create -n rivesaltes python=3.6
source activate rivesaltes
```

download the package

```
cd rivesaltes
pip install -r requirements.txt
pip install . 
```

# AWS credentials
```
mkdir ~/.aws
cd ~/.aws 
```
you need to create here two files _config_ and _credentials_

__config content__
```
[default]
region=eu-west-1
```

__credentials content__
```
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

# Docker test & deployment

## Download DataDriver containers

1) `aws configure with your credentials`
2) `$(aws ecr get-login --no-include-email --region eu-west-1)`
3) `docker pull 969076149354.dkr.ecr.eu-west-1.amazonaws.com/dd/database:latest`
4) `docker pull 969076149354.dkr.ecr.eu-west-1.amazonaws.com/dd/factory:latest`

## Build images

```
$ docker-compose build
```

## Run application server

```
$ docker-compose up
```

## Add a new worker

```
$ docker-compose scale rivesaltes_worker=2
```

## Run tests

Acceptance tests
```
$ make acceptance_test
```

Unit tests

```
$ make unittest
```

All tests

```
$ make test
```


# Rivesaltes WEBAPP

## Getting Started

Update the environment variables in *docker-compose.yml*, and then build the images and spin up the containers:

```sh
$ docker-compose up -d --build
```

Create the database:

```sh
$ docker-compose run web python manage.py create_db
$ docker-compose run web python manage.py db init
$ docker-compose run web python manage.py db migrate
$ docker-compose run web python manage.py create_admin
$ docker-compose run web python manage.py create_data
```

Access the application at the address [http://localhost:5002/](http://localhost:5002/)

### Testing

Test without coverage:

```sh
$ docker-compose run web python manage.py test
```

Test with coverage:

```sh
$ docker-compose run web python manage.py cov
```

Lint:

```sh
$ docker-compose run web flake8 project
```



# TODO
## Conf file
add prefix in configuration file

## HookS3 à définir à la main 
penser à mettre les credentials aws dans le webserver "connexion", 
sous le nom "octo-rivesaltes" > peut être le mettre dans la conf ? 

## Tools
pour le rall back de ceux qu'on a en raw et pas en processed

