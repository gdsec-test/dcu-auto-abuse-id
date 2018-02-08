import os
import logging.config
import yaml
from service.rest import create_app

app = create_app()

if __name__ == '__main__':
    path = os.path.dirname(os.path.abspath(__file__)) + '/' + 'logging.yml'
    value = os.getenv('LOG_CFG', None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            lconfig = yaml.safe_load(f.read())
        logging.config.dictConfig(lconfig)
    else:
        logging.basicConfig(level=logging.INFO)
    logging.raiseExceptions = True
    app.run()
