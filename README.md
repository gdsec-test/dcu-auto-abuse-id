# Auto Abuse ID
Project to programmatically identify which content is abusive.  Open API Spec for REST Endpoints: https://classify.int.godaddy.com/doc
To run from this swagger spec, you'll need to auth with a current JWT from a user in one of the groups identified [here](https://github.secureserver.net/digital-crimes/auto_abuse_id/blob/master/settings.py#L19)

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

    curl --location --request POST 'http://127.0.0.1:5000/classify/classification' \
    --header 'Authorization: sso-jwt YOUR_JWT' \
    --header 'Content-Type: application/json' \
    --data '{"uri": "http://yahoo.com"}'

>Note: If running as `test`, you should see activity in the `testclassify_tasks` Rabbit queue ([web browser link here](http://rmq-dcu.int.godaddy.com:15672/#/))... however, the message will remain there if there are no consumers.  By setting the "Ack Mode" to "Ack message requeue false", you can view the message while removing it from the queue.

The result will contain a job id `id`.  Use that `id` in the next call, which will return classification results:

    curl --location --request GET 'http://127.0.0.1:5000/classify/classification/JID' \
    --header 'Authorization: sso-jwt YOUR_JWT'

## CURL test on PROD
To run from this against prod, you'll need to auth with a current JWT from a user in one of the groups identified [here](https://github.secureserver.net/digital-crimes/auto_abuse_id/blob/master/settings.py#L19)

To request classification of a URI in prod, run the following curl command:

    curl --location --request POST 'https://classify.int.godaddy.com/classify/classification' \
    --header 'Authorization: sso-jwt YOUR_JWT' \
    --header 'Content-Type: application/json' \
    --data '{"uri": "http://impcat.com"}'

The result should resemble:

    {
       "status": "PENDING",
       "confidence": 0.0,
       "candidate": "http://beandejo.com",
       "id": "1cde74c5-ba92-4647-a5ff-f423f313da8d"
    }

The result will contain a job id `id`.  Use that `id` in the next call, which will return classification results:

    curl --location --request GET 'https://classify.int.godaddy.com/classify/classification/1cde74c5-ba92-4647-a5ff-f423f313da8d' \
    --header 'Authorization: sso-jwt YOUR_JWT'

The result should resemble:

    {
       "status": "SUCCESS",
       "confidence": 0.0,
       "candidate": "http://beandejo.com",
       "id": "1cde74c5-ba92-4647-a5ff-f423f313da8d"
    }
