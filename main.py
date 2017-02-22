import datetime
import logging
import json
import os
import re
import urllib
import requests
import tweepy
import praw
from keys import twitter_keys
from keys import reddit_keys
from apscheduler.scheduler import Scheduler

# scheduler
logging.basicConfig()
sched = Scheduler(standalone=True)
sched.daemonic = False

# twitter API
CONSUMER_KEY = twitter_keys['consumer_key']
CONSUMER_SECRET = twitter_keys['consumer_secret']
ACCESS_TOKEN = twitter_keys['access_token']
ACCESS_TOKEN_SECRET = twitter_keys['access_token_secret']

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
twitterApi = tweepy.API(auth)

SUBREDDIT = 'aww'
IMAGEURLS_FILENAME = 'links.json'

# reddit API
redditApi = praw.Reddit(
	client_id = reddit_keys['client_id'],
	client_secret = reddit_keys['client_secret'],
	user_agent = reddit_keys['user_agent']
	)

def checkIfImageAlreadyTweeted(url):
	fr = open(IMAGEURLS_FILENAME, 'r')
	text = fr.read()

	if url not in text:
		return False

		return True

# DOWNLOAD IMAGE URL
def download_media(image_url):
	image_url = image_url.replace('gifv', 'mp4')

	filename = image_url.split('/')[-1]
	filepath = "downloads/img." + image_url.split('/')[-1].split('.')[-1]

	# get the filesize via header
	head = requests.head(image_url)
	filesizeInKb = float(head.headers['Content-Length'])/1000.0
	
	# check if greater than twitter API filesize upload limit
	if filesizeInKb > 3072:
		print("Filesize greater than 3072")
		return

	# download the image
	print('Downloading ' + filename + '...')
	response = requests.get(image_url)

	if response.status_code == 200:
		with open(filepath, 'wb+') as fo:
			for chunk in response.iter_content(4096):
				fo.write(chunk)

		fw = open(IMAGEURLS_FILENAME, 'a')
		fw.write(str(filename) + '\n')
		return filepath

	# filename = filename.replace('gifv', 'gif')
	# urllib.urlretrieve(image_url, "downloads/" + filename)

def isValidImageUrl(url):
	imagePattern = re.compile(r".*\.(jpg|png|jpeg)$")
	return imagePattern.match(url)

def addUrlsToQueueFile(urls):
	with open(IMAGEURLS_FILENAME, 'r+') as f:
		jsonData = json.load(f)

		for url in urls:
			jsonData['queue'].append(url)

		jsonData['queue'] = list(set(jsonData['queue']) - set(jsonData['done']))

		f.seek(0)
		f.write(json.dumps(jsonData))
		f.truncate()

def getImageUrlsAndQueue():
	imgUrls = []

	print("Downloading urls...")
	for s in redditApi.subreddit(SUBREDDIT).hot(limit=100):

		if not isValidImageUrl(s.url):
			continue

		print("http://reddit.com" + s.permalink)

		imgUrls.append(s.url)
		# end for

	addUrlsToQueueFile(imgUrls)

	#end getImageUrlsAndQueue

def tweetFromQueue():
	print("Running tweetFromQueue()")
	with open(IMAGEURLS_FILENAME, 'r+') as f:
		linksJson = json.load(f)

		if not linksJson['queue']:
			print("Queue is now empty! Fetching urls...")
			getImageUrlsAndQueue()
			tweetFromQueue()
			return

		# get the first image url from the queue array
		imageUrl = linksJson['queue'][0]
		if not imageUrl:
			return

		downloaded_filename = download_media(imageUrl)

		# remove that item from the array
		linksJson['done'].append(linksJson['queue'].pop(0))
		f.seek(0)
		f.write(json.dumps(linksJson))
		f.truncate()

		# tweet it
		if downloaded_filename:
			print("Tweeting: " + imageUrl)
			twitterApi.update_with_media(downloaded_filename)

		print("Tweeted!")

def searchAndLike():
	print('Searching and liking tweets...')
	count = 0

	query = 'dogs cute'
	max_tweets = 10

	for tweet in tweepy.Cursor(twitterApi.search, q=query, include_entities=True).items(max_tweets):
		try:
			twitterApi.create_favorite(tweet.id)
			print("[/] " + tweet.text)
			count += 1
		except tweepy.TweepError as e:
			print(e.message[0]['message'] + ' :: ' + tweet.id)

	print(bcolors.ENDC + '--- ' + str(count) + ' tweets liked. ---\n')

# START
print "--- RUNNING DOGGIES BOT ---"
sched.add_cron_job(tweetFromQueue, minute='0,30')
sched.add_cron_job(searchAndLike, minute='15,45')

try:
	sched.start()
except KeyboardInterrupt:
    print('Got SIGTERM! Terminating...')
except Exception as e:
	print(e)