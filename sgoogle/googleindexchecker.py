#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
# Mai Xuan Trang
# 
#

from browser import BrowserError, Browser
from urllib import urlencode
from scrapy.selector import Selector
from scraper import GoogleScraper





class URLIdexed(object):
    def __init__(self, url, indexed):
        self.url = url
        self.indexed = indexed

class IndexChecker(object):
    def __init__(self, urls, tld="com"):
        self.urls = urls
        self.tld = tld
    def check(self):
        checkedurls = []
        for url in self.urls:
            query = 'info:'+url
            scraper = GoogleScraper(query, debug=True, random_agent=False)
            titles = scraper.get_google_search_result()
            indexed = 'No'
            if titles:
                indexed = 'Yes'
            urlindexed = URLIdexed(url, indexed)
            checkedurls.append(urlindexed)
        return checkedurls





