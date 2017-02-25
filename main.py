#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import logging
import json
import sys
import os
import re
import urllib
import requests
import tweepy
import praw
from keys import twitter_keys
from keys import reddit_keys
from apscheduler.scheduler import Scheduler
from config import config
from pprint import pprint

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

# FOR TESTING
# switch to False on prod
DEVELOPMENT_MODE = config['development_mode']

SUBMISSION_QUEUE_FILENAME = 'links.json'

# reddit API
redditApi = praw.Reddit(
	client_id = reddit_keys['client_id'],
	client_secret = reddit_keys['client_secret'],
	user_agent = reddit_keys['user_agent']
	)

def checkIfImageAlreadyTweeted(url):
	fr = open(SUBMISSION_QUEUE_FILENAME, 'r')
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

		fw = open(SUBMISSION_QUEUE_FILENAME, 'a')
		fw.write(str(filename) + '\n')
		return filepath

	# filename = filename.replace('gifv', 'gif')
	# urllib.urlretrieve(image_url, "downloads/" + filename)

def isValidImageUrl(url):
	imagePattern = re.compile(r".*\.(jpg|png|jpeg)$")
	return imagePattern.match(url)

def getSubmissionsAndQueue():
	submissions = {}

	print("Downloading submissions...")

	with open(SUBMISSION_QUEUE_FILENAME, 'r+') as f:
		jsonData = json.load(f)

		hot_submissions = redditApi.subreddit(config['subreddit']).hot(limit=100)

		# loop all hot submissions and save them to queue
		for submission in hot_submissions:
			if config['image_submissions_only'] and not isValidImageUrl(submission.url):
				continue

			if not submission.id in jsonData['done']:
				jsonData['queue'][submission.id] = {
					'title': submission.title,
					'permalink': "http://reddit.com" + submission.permalink,
					'image_url': submission.url
				}
			# end for

		f.seek(0)
		f.write(json.dumps(jsonData))
		f.truncate()

	#end getSubmissionsAndQueue

def tweetFromQueue():
	print("Running tweetFromQueue()")
	with open(SUBMISSION_QUEUE_FILENAME, 'r+') as f:
		linksJson = json.load(f)

		if not linksJson['queue']:
			print("Queue is now empty! Fetching submissions...")
			getSubmissionsAndQueue()
			tweetFromQueue()
			return

		# pop the first submission object from the queue
		submissionId, submission = linksJson['queue'].popitem()

		if not submission:
			return

		downloaded_filename = download_media(submission['image_url'])

		# add the submission to "done"
		linksJson['done'][submissionId] = submission
		f.seek(0)
		f.write(json.dumps(linksJson))
		f.truncate()

		# tweet it
		if downloaded_filename:
			print("Tweeting: " + submission['permalink'])

			if not DEVELOPMENT_MODE:
				if config['tweet_with_title']:
					print("Tweeted with title!")
					twitterApi.update_with_media(downloaded_filename, status=submission['title'])
				else:
					print("Tweeted image only!")
					twitterApi.update_with_media(downloaded_filename)
			else:
				print(submission['title'] + ' :: ' + downloaded_filename)
				print("Tweeted but not really!")

		print("Queue: " + str(len(linksJson['queue'])) + " / Done: " + str(len(linksJson['done'])))

def searchAndLike():
	print('Searching and liking tweets...')
	count = 0

	query = config['autoliker_search_query']
	max_tweets = config['autoliker_max_tweets']

	for tweet in tweepy.Cursor(twitterApi.search, q=query, include_entities=True).items(max_tweets):
		try:
			if not DEVELOPMENT_MODE:
				twitterApi.create_favorite(tweet.id)
				print("Liked: " + unicode(tweet.text))
			else:
				print("Liked but not really: " + unicode(tweet.text))

			count += 1
				
		except tweepy.TweepError as e:
			print(e)
			print(e.message[0]['message'] + ' :: ' + str(tweet.id))
			sys.exit(0)

	print('--- ' + str(count) + ' tweets liked. ---\n')

def start():
	print "--- RUNNING r/" + config['subreddit'] + " BOT ---"
	sched.add_cron_job(tweetFromQueue, minute=config['tweet_cron_minute'])

	if config['autoliker_enabled'] and not DEVELOPMENT_MODE:
		print "Running autoliker for: " + config['autoliker_search_query'] + "..."
		sched.add_cron_job(searchAndLike, minute=config['autoliker_cron_minute'])

	try:
		sched.start()
	except KeyboardInterrupt:
	    print('Got SIGTERM! Terminating...')
	except Exception as e:
		print(e)

# START SCRIPT
start()