# SAV Worker

the Worker module contains 3 separate workers.

## Dependencies

the main dependencies of this project is the SAV-APP module `python`, `rabbitmq` and lastly `posgreSQL` database the same as the SAV-APP module

run to install all python project dependencies
```
pip install -r requirements.txt
```

## Configuration

the workers expect the postgres database URL to be in an environmental variable `POSTGRES_URL` and expects rabbitmq to be running on the same machine but can be Configured to run on a remote host.

## Running

first start the sav-app module, check it's repo to know how to run it

start rabbitmq as sudo

```
sudo rabbitmq-server
```

then start each of the three workers and wait for them to finish initialization

```
python initialization.py
python classify.py
python extract.py
```
