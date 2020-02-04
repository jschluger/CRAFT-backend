# parse command line arguments
import argparse, os
parser = argparse.ArgumentParser()
parser.add_argument('--start_from_backup', default=False, action='store_true',
    help='Include to load the backup files as the initial state of the data structures.')
args = parser.parse_args()

import data
from server import app
from utils import live_download, backups

data.args = args

if __name__ == '__main__':
    if data.args.start_from_backup:
        backups.load_backup()
        print('Loaded backup...')
        backups.check_data()
    elif os.path.isdir(data.CORPUS_f):
        print( '--------------------------ERROR---------------------------------\n'
               'Did not pass --start_from_backup, but backup files already exist.\n'
               'Pass --start_from_backup to use backed up data, or move backup\n'
              f' files {data.SCORES_f} and {data.POSTS_f} to start from scratch.\n'
               '--------------------------ERROR---------------------------------')
        exit(1)


    live_download.maintain_corpus()
    
    # start the flask app!
    app.run(host='0.0.0.0', port=8080, use_reloader=False)
    
