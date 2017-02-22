#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
from config import config

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
DEVELOPMENT_MODE = True

SUBREDDIT = config['subreddit']
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

			if not DEVELOPMENT_MODE:
				print("Tweeted!")
				twitterApi.update_with_media(downloaded_filename)
			else:
				print("Tweeted but not really!")

def searchAndLike():
	print('Searching and liking tweets...')
	count = 0

	query = config['autoliker_search_query']
	max_tweets = config['autoliker_max_tweets']

	for tweet in tweepy.Cursor(twitterApi.search, q=query, include_entities=True).items(max_tweets):
		try:
			if not DEVELOPMENT_MODE:
				twitterApi.create_favorite(tweet.id)
				print("Liked: " + tweet.text)
			else:
				print("Liked but not really: " + tweet.text)

			count += 1
				
		except tweepy.TweepError as e:
			print(e.message[0]['message'] + ' :: ' + tweet.id)

	print('--- ' + str(count) + ' tweets liked. ---\n')

# START
print "--- RUNNING DOGGIES BOT ---"
sched.add_cron_job(tweetFromQueue, minute=config['tweet_cron_minute'])
sched.add_cron_job(searchAndLike, minute=config['autoliker_cron_minute'])

try:
	sched.start()
except KeyboardInterrupt:
    print('Got SIGTERM! Terminating...')
except Exception as e:
	print(e)