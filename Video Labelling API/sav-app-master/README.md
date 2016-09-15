# SAV App

the main API and application for the SAV project

## Dependencies

first install all the front-end and back-end dependencies using node & bower (if they are not installed check the project page on how to install them)
```
npm install
bower install
```
install sailsjs globaly using node
```
sudo npm install -g sails
```

Other dependencies include `redis`, `rabbitmq` and `postgreSQL`

## Configuration

please refer to sails documentation on how to configure the project's database and running port
the project expects redis and rabbitmq to be on the localhost but you can configure them otherwise.

## Running

first start redis then start the project using sails
```
sudo redis
sails lift
```

## Usage

currently the application provides the following API endpoints

generate a user and a token using the web application running at `localhost`

```
// for authenticating takes parmas: email, password, token
'post /api/v1/login'
// checking for authentication params: token
'get /api/v1/isauthenticated'
// for pushing a job params: data (file), name, token
'post /api/v1/pushjob'
// getting job info params: id, token
'get /api/v1/jobinfo'
// getting all jobs information, params: token
'get /api/v1/jobs'
// search for a label params: token, id, search
'get /api/v1/search'
```
