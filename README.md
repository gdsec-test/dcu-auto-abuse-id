# Auto Abuse ID
Project to programmatically identify which content is abusive

 ## Cloning
 To clone the repository via SSH perform the following
 ```
 git clone git@github.secureserver.net:ITSecurity/auto_abuse_id.git
 ```

 It is recommended that you clone this project into a pyvirtualenv or equivalent virtual environment.

## Installing Dependencies
You can install the required private dependencies via
```
pip install -r private_pips.txt
```
Followed by installing public dependencies via
```
pip install -r requirements.txt
```

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
 In order to run the tests you must first install the required dependencies via
 ```
 pip install -r test_requirements.txt
 ```

 After this you may run the tests via
 ```
 nosetests tests/
 ```

 Optionally, you may provide the flags `--with-coverage --cover-package=service/` to `nosetests` to determine the test coverage of the project.

 ## Built With
 Auto Abuse ID is built utilizing the following key technologies
 1. dcdatabase
 
## Running Locally
 If you would like to run auto_abuse_id locally you will need to specify the following environment variables
 1. `sysenv` (dev, ote, prod)
 
### usage:
`curl -XPUT -H "Content-Type: application/json" http://localhost:5000/classify/submit_uri -d '{"uri": "https://godaddy.com"}'`
