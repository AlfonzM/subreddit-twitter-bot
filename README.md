# subreddit-twitter-bot

Twitter bot that crawls for "hot" submissions of a specified subreddit and tweets them.

## Usage

```
pip install -r requirements.txt
mv config.py.example config.py
vim config.py

# edit config, add twitter and reddit keys

python main.py
```

## Deploy to Heroku

After logging in in heroku cli:

```
heroku git:remote -a APP_NAME
git add .
git commit -m "Add features"
git push heroku master
```

Check logs with:

```
heroku logs —app APP_NAME —tail
```
