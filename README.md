# Auto Abuse ID
Project to programmatically identify which content is abusive

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
If you would like to run auto_abuse_id locally you will need to specify the following environment variables
1. `sysenv` (dev, ote, prod)
 
### usage:
`curl -XPUT -H "Content-Type: application/json" http://localhost:5000/classify/submit_uri -d '{"uri": "https://godaddy.com"}'`
