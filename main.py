import tweepy
import praw
from keys import twitter_keys
from keys import reddit_keys

# twitter API
CONSUMER_KEY = twitter_keys['consumer_key']
CONSUMER_SECRET = twitter_keys['consumer_secret']
ACCESS_TOKEN = twitter_keys['access_token']
ACCESS_TOKEN_SECRET = twitter_keys['access_token_secret']

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
twitterApi = tweepy.API(auth)

# reddit API
redditApi = praw.Reddit(
	client_id = reddit_keys['client_id'],
	client_secret = reddit_keys['client_secret'],
	user_agent = reddit_keys['user_agent']
)

print redditApi.subreddit('aww')