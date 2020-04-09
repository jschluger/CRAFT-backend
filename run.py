from gevent import monkey
monkey.patch_all()

import data
from server import app
from utils import live_download, scheduled, backups
from gevent import pywsgi
import argparse
import os
import time


# parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--start_from_backup', default=False, action='store_true',
                    help='Include to load the backup files as the initial state of the data structures.')
args = parser.parse_args()


data.args = args


if __name__ == '__main__':
    if data.args.start_from_backup:
        entered = time.time()
        print('Loading backups...')
        backups.load_backup()
        print(f'\t\t...backups loaded {time.time() - entered} seconds')
    elif os.path.isdir(data.CORPUS_f):
        print(data.CORPUS_f)
        print('--------------------------ERROR---------------------------------\n'
              'Did not pass --start_from_backup, but backup files already exist.\n'
              'Pass --start_from_backup to use backed up data, or move backup\n'
              ' files to start from scratch.\n'
              '--------------------------ERROR---------------------------------')
        exit(1)

    live_download.maintain_corpus()
    scheduled.setup()

    live_download.ingest_wiki_corpus()

    # start the flask app!
    # app.run(host='0.0.0.0', port=8080, use_reloader=False)

    server = pywsgi.WSGIServer(listener=('0.0.0.0', 8080), application=app)
    print('Starting the server!')
    server.serve_forever()
