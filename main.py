import json
import os
import re
import urllib
import requests
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

SUBREDDIT = 'aww'
IMAGE_URL_LIST = 'links.json'

# reddit API
redditApi = praw.Reddit(
	client_id = reddit_keys['client_id'],
	client_secret = reddit_keys['client_secret'],
	user_agent = reddit_keys['user_agent']
	)

def checkIfImageAlreadyTweeted(url):
	fr = open(IMAGE_URL_LIST, 'r')
	text = fr.read()

	if url not in text:
		return False

		return True

# DOWNLOAD IMAGE URL
def download_media(image_url):
	image_url = image_url.replace('gifv', 'mp4')

	filename = image_url.split('/')[-1]
	filepath = "downloads/" + image_url.split('/')[-1]

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
		with open(filepath, 'wb') as fo:
			for chunk in response.iter_content(4096):
				fo.write(chunk)

		fw = open(IMAGE_URL_LIST, 'a')
		fw.write(str(filename) + '\n')
		return filepath

	# filename = filename.replace('gifv', 'gif')
	# urllib.urlretrieve(image_url, "downloads/" + filename)

def isValidImageUrl(url):
	imagePattern = re.compile(r".*\.(jpg|png|jpeg)$")
	return imagePattern.match(url)

def addToQueue(urls):
	for url in urls:
		with open('links.json', 'r') as f:
			jsonData = json.load(f)
			jsonData['queue'].append(url)

		with open('links.json', 'w') as f:
			f.write(json.dumps(jsonData))

def getImageUrlsAndQueue():
	imgUrls = []

	for s in redditApi.subreddit(SUBREDDIT).hot(limit=5):
		print('---')
		print(s.url)

		if not isValidImageUrl(s.url):
			print ('NOT IMAGE')
			continue

		print("http://reddit.com" + s.permalink)

		imgUrls.append(s.url)
		# end for

	addToQueue(imgUrls)

	#end getImageUrlsAndQueue

def tweetFromQueue():
	with open('links.json', 'r+') as f:
		linksJson = json.load(f)

		# get the first image url from the queue array
		if not linksJson['queue']:
			print("Queue is empty! Fetching urls")
			getImageUrlsAndQueue()
			tweetFromQueue()
			return

		imageUrl = linksJson['queue'][0]

		if not imageUrl:
			return
			
		downloaded_filename = download_media(imageUrl)

		# remove that item from the array
		linksJson['queue'].pop(0)
		f.seek(0)
		f.write(json.dumps(linksJson))
		f.truncate()

		# tweet it
		print("tweeting...")
		if downloaded_filename:
			twitterApi.update_with_media(downloaded_filename, status='hai')

	print('done')
	
# getImageUrlsAndQueue()
tweetFromQueue()