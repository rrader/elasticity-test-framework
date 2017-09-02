import json
from random import choice

import redis
from flask import Flask, request
from pidigits import getPi


# Lib


class MemoryStorage:
    def __init__(self, app):
        self.articles = []

    def get_articles(self):
        return self.articles

    def add_article(self, title, body):
        self.articles.append(dict(
            title=title,
            body=body
        ))


class RedisStorage:
    def __init__(self, app):
        self.master = redis.ConnectionPool.from_url(app.config['REDIS_MASTER'])
        self.key = 'BLOG_POSTS'
        self.pools = []
        for redis_url in app.config['REDISES'].split(','):
            self.pools.append(redis.ConnectionPool.from_url(redis_url))

    @property
    def conn_w(self):
        return redis.StrictRedis(connection_pool=self.master)

    @property
    def conn_r(self):
        return redis.StrictRedis(connection_pool=choice(self.pools))

    def get_articles(self):
        return [
            json.loads(a.decode()) for a in
            self.conn_r.lrange(self.key, 0, -1)
        ]

    def add_article(self, title, body):
        val = json.dumps(dict(
            title=title,
            body=body
        ))
        self.conn_w.lpush(self.key, val)


# Templates

BASE = """
<!DOCTYPE html>
<html>
   <head>
      <meta charset="utf-8">
      <title>
         Blog
      </title>
   </head>
   <body>
      <header>
         <hgroup>
            <h1>
               The Blog
            </h1>
         </hgroup>
      </header>
      <section>
         <form action="/add" method="POST">
            <p>Title: <input type="input" name="title" value=""></p>
            <p>Body: <textarea name="body" cols="40" rows="5"></textarea></p>
            <p><input type="submit" value="ADD"></p>
         </form>
      </section>
      <section>
         {content}
      </section>
      <hr/>
      <footer>
        Elasticity Test
      </footer>
   </body>
</html>
"""
ARTICLE = """
         <article>
            <h1>
               {title}
            </h1>
            <p>
               {body}
            </p>
         </article>
"""

# App

app = Flask(__name__)
app.config.from_json('config.json')
if app.config['STORAGE'] == 'redis':
    storage = RedisStorage(app)
else:
    storage = MemoryStorage(app)


@app.route("/", methods=['GET'])
def records():
    getPi(100)
    return BASE.format(
        content=''.join(ARTICLE.format(**a) for a in storage.get_articles())
    )


@app.route("/add", methods=['POST'])
def add_record():
    data = request.form
    storage.add_article(data['title'], data['body'])
    return BASE.format(
        content='<b>DONE!</b>'
    )
