# parse command line arguments
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--start_from_backup', default=False, action='store_true',
    help='Include to load the backup files as the initial state of the data structures.')
args = parser.parse_args()

import data
from server import app
from utils import update

data.args = args

if __name__ == '__main__':
    # setup regularly scheduled updates and possibly load data from backup
    update.setup()
    
    # start the flask app!
    app.run(host='0.0.0.0', port=8080, use_reloader=False)
    
