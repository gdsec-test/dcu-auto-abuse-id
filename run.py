import os
from service.rest import create_app

env = os.getenv('sysenv') or 'dev'
app = create_app(env)

if __name__ == '__main__':
    app.run()
