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
# update at the top of each minute where the number of minutes in the time is divisible by 5
update_cron = {'minute': '*/5'}

##############################################################
# constants & data structures needed for application, Do Not Modify
##############################################################
WIKI_CORPUS = None
WIKI_COMMENTS = {}
WIKI_TOPICS = ["Punk", "Guy_Fieri", "Conversation"]
WIKI_RECEIVED = []

CORPUS = None
POSTS = {}
RECIEVED = []
TIMES = {}

RECIEVED_f = 'data/recieved.pkl'
TIMES_f = 'data/times.pkl'
POSTS_f = 'data/posts.pkl'
CORPUS_f = 'data/live-rCMV-corpus'

SEC_PER_HOUR = 60 * 60
SEC_PER_DAY = SEC_PER_HOUR * 24

THRESHOLD = 0.548580

reddit = praw.Reddit(client_id='sq6GgQR_4lri7A',
                     client_secret='dWes213OfQWpF7eCVxeImaHSbiw',
                     user_agent='jack')


args = None  # will become the command line arguments
