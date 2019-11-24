from server import app
from utils import update


if __name__ == '__main__':
    # setup regularly scheduled updates and start the flask app!
    update.setup()    
    app.run(host='0.0.0.0', port=8080, use_reloader=False)
    
    
