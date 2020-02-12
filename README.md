# Auto Abuse ID
Project to programmatically identify which content is abusive.  Open API Spec for REST Endpoints: https://classify.int.godaddy.com/doc

## Cloning
To clone the repository via SSH perform the following
```
git clone git@github.secureserver.net:digital-crimes/auto_abuse_id.git
```

It is recommended that you clone this project into a pyvirtualenv or equivalent virtual environment.

## Installing Dependencies
To install all dependencies for development and testing simply run `make`.

## Building
Building a local Docker image for the respective development environments can be achieved by
```
make [dev, ote, prod]
```

## Deploying
Deploying the Docker image to Kubernetes can be achieved via
```
make [dev, ote, prod]-deploy
```
You must also ensure you have the proper push permissions to Artifactory or you may experience a `Forbidden` message.

## Testing
```
make test     # runs all unit tests
make testcov  # runs tests with coverage
```

## Style and Standards
All deploys must pass Flake8 linting and all unit tests which are baked into the [Makefile](Makfile).

There are a few commands that might be useful to ensure consistent Python style:

```
make flake8  # Runs the Flake8 linter
make isort   # Sorts all imports
make tools   # Runs both Flake8 and isort
```

## Built With
Auto Abuse ID is built utilizing the following key technologies
1. dcdatabase
 
## Running Locally
If you would like to run auto_abuse_id locally, you will need to specify the following environment variables
1. `sysenv` (test, dev, ote, prod)
   1. If running as `test`, you'll need an instance of MongoDB running on port 27017 and an instance of Redis Server running on port 6379.  MongoDB will need to have a `devphishstory` database with a `test` collection contained within it.  There should be no mongodb authentication.
2. `BROKER_PASS` RabbitMQ password for the `02d1081iywc7A` user
3. `DB_PASS` if running with a `dev`, `ote` or `prod` value for `sysenv`
 
### usage:
To request clasification of a URI, run the following curl command:

`curl -XPOST -H "Content-Type: application/json" http://localhost:5000/classify/classification -d '{"uri": "https://godaddy.com"}'`

The result will contain a job id `JID`.  Use that JID in the next call, which will return classification results:

`curl -H "accept: application/json" http://localhost:5000/classify/classification/JID`
