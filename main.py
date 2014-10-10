#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import urllib2
import json
from django.utils import feedgenerator
from datetime import datetime
import lxml.html


def strimwidth(s, length, dash='...'):
    return s[:length] + dash if len(s) > length else s


class MainHandler(webapp2.RequestHandler):
    def get(self, id):
        url = 'http://cdn.syndication.twimg.com/widgets/timelines/' + id
        result = urllib2.urlopen(url)
        jsonobject = json.load(result)

        if 'body' not in jsonobject:
            self.response.write(jsonobject['headers']['message'])
            return

        body = jsonobject['body']

        kind = self.request.get('kind', 'rss')
        if kind == 'atom':
            fncfeed = feedgenerator.Atom1Feed
        elif kind == 'rss':
            fncfeed = feedgenerator.Rss201rev2Feed
        elif kind == 'html':
            self.response.write(body)
            return

        root = lxml.html.fromstring(body)

        h2 = root.xpath('//h2/text()')
        listdesc = root.xpath('//p[@class="list-description"]/text()')

        feed = fncfeed(
            title=root.xpath('//h1/a/text()')[0],
            link=root.xpath('//h1/a/@href')[0],
            description=listdesc[0] if listdesc else h2[0] if h2 else '',
            language='ja'
        )

        for li in root.xpath('//ol[@class="h-feed"]/li'):

            title = li.xpath('.//p[@class="e-entry-title"]')[0]
            imgsrc = li.xpath('.//img[@class="u-photo avatar"]/@src')[0]
            desc = '<img src="%s">' % imgsrc
            desc += lxml.html.tostring(title)

            retweet = li.xpath('.//div[@class="retweet-credit"]/a')
            if retweet:
                desc += '<br/>\n( Retweeted by %s )' % lxml.html.tostring(retweet[0])

            feed.add_item(
                title=strimwidth(title.text_content(), 30),
                link=li.xpath('.//a/@href')[0],
                description=desc,
                author_name=li.xpath(
                    './/span[@class="full-name"]/span/text()')[0],
                author_email=li.xpath(
                    './/span[@class="p-nickname"]/b/text()')[0],
                author_link=li.xpath(
                    './/a[@class="u-url profile"]/@href')[0],
                pubdate=datetime.strptime(
                    li.xpath('.//time/@datetime')[0],
                    '%Y-%m-%dT%H:%M:%S+0000')
            )

        self.response.headers['Content-Type'] = 'text/xml; charset=utf-8'
        self.response.write(feed.writeString('utf-8'))

app = webapp2.WSGIApplication([
    ('/feed/(\d+)', MainHandler)
], debug=True)
