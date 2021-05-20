import os

from service.rest import create_app
from settings import config_by_name

config = config_by_name[os.getenv('sysenv', 'dev')]()
app = create_app(config)

if __name__ == '__main__':
    app.run()
