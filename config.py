config = dict(
	subreddit = 'aww',
	tweet_cron_minute = '0,30', # cron minute for tweet (e.g. '15,45' will run tweetFromQueue every x:15 and x:45)
	autoliker_cron_minute = '15,45', # cron minute for autoliker (e.g. '15,45' will run autoliker every x:15 and x:45)
	autoliker_max_tweets = 25, # max tweets to like every time searchAndLike is run
	autoliker_search_query = 'dogs cute'
)