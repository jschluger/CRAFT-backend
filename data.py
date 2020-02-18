from convokit import Corpus, Utterance, User
import praw
##################################################################
# Set these variables to configure the behavior of the application
################################################################## 

# p is number of posts to dowload from reddit on each update
# p = 25

# run craft is whether or not an update runs craft or uses dummy prediction scores.
run_craft = True

# update_cron is the cron schedule for updates, passed as arguments to scheduler.add_job
# See documentation here: https://apscheduler.readthedocs.io/en/stable/modules/triggers/cron.html
# Uncomment the line you want! 
# update_cron = {'second': '*/20' } # update at each time where the number of seconds is divisable by 20
# update_cron = {'second': 0} # update at the top of each minute
# update_cron = {'minute': 56} # update at the top of each hour
update_cron = {'minute': '*/5'} # update at the top of each minute where the number of minutes in the time is divisible by 20

##############################################################
# data & data structures needed for application, Do Not Modify
##############################################################
# SCORES = {}
# POSTS  = {}
# ACTIVE = {}

CORPUS = None
COMMENTS = {}
RECIEVED = []
TIMES = {}

RECIEVED_f = 'data/recieved.pkl'
TIMES_f  = 'data/times.pkl'
CORPUS_f = 'data/live-rCMV-corpus'

reddit = praw.Reddit(client_id='sq6GgQR_4lri7A',
                     client_secret='dWes213OfQWpF7eCVxeImaHSbiw',
                     user_agent='jack')


args = None # will become the command line arguments
