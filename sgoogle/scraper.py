#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
# Mai Xuan Trang
# 
#

import re
import urllib
import urllib2
from datetime import datetime
import lxml
from htmlentitydefs import name2codepoint
from Queue import Queue
from browser import Browser, BrowserError
import ssl
import os
from pathos.multiprocessing import ProcessingPool as Pool
import multiprocessing
import justext
import logging
import sys
from scrapy.selector import Selector
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
# from boilerpipe.extract import Extractor

reload(sys)  
sys.setdefaultencoding('utf8')

LENGTH_LOW_DEFAULT = 100

TITLE_XPATH_DESKTOP = '//div[@class="rc"]/h3/a/text()'
URL_XPATH_DESKTOP = '//div[@class="rc"]/h3/a/@href'
DESC_XPATH_DESKTOP = '//div[@class="rc"]/div[@class="s"]/div/span/text()[last()]'

TITLE_XPATH_MOBILE = '//div[@class="rc"]/div/h3/a/text()'
URL_XPATH_MOBILE = '//div[@class="rc"]/div/h3/a/@href'
DESC_XPATH_MOBILE= '//div[@class="rc"]/div[@class="s"]/div/span/text()[last()]'

class ScraperError(Exception):
    """
    Base class for Google Search exceptions.
    """
    pass

class ParseError(ScraperError):
    """
    Parse error in Google results.
    self.msg attribute contains explanation why parsing failed
    self.tag attribute contains BeautifulSoup object with the most relevant tag that failed to parse
    Thrown only in debug mode
    """
     
    def __init__(self, msg, tag):
        self.msg = msg
        self.tag = tag

    def __str__(self):
        return self.msg

    def html(self):
        return self.tag.prettify()

class SearchResult:
    def __init__(self, titles, urls, descs, contents):
        self.titles = titles
        self.urls = urls
        self.descs = descs
        self.contents = contents

    def __str__(self):
        return 'Google Search Result: "%s"' % self.titles

class URLResult:
    def __init__(self, url, searchorder):
        self.url = url
        self.searchorder = searchorder
    def __str__(self):
        return self.url

class Content:
    def __init__(self, url, text):
        self.url = url
        self.text = text
    def __str__(self):
        return self.text

class GoogleScraper(object):
    SEARCH_URL_0 = "http://www.google.%(tld)s/search?hl=%(lang)s&q=%(query)s&btnG=Google+Search"
    NEXT_PAGE_0 = "http://www.google.%(tld)s/search?hl=%(lang)s&q=%(query)s&start=%(start)d"
    SEARCH_URL_1 = "http://www.google.%(tld)s/search?hl=%(lang)s&q=%(query)s&num=%(num)d&btnG=Google+Search"
    NEXT_PAGE_1 = "http://www.google.%(tld)s/search?hl=%(lang)s&q=%(query)s&num=%(num)d&start=%(start)d"

    def __init__(self, query, random_agent=False, debug=False, lang="en", tld="com", re_search_strings=None, mobile=False):
        self.query = query
        self.debug = debug
        self.browser = Browser(debug=debug)
        self.results_info = None
        self.eor = False # end of results
        self._page = 0
        self._first_indexed_in_previous = None
        self._filetype = None
        self._last_search_url = None
        self._results_per_page = 10
        self._last_from = 0
        self._lang = lang
        self._tld = tld
        self.mobile = mobile
        
        if re_search_strings:
            self._re_search_strings = re_search_strings
        elif lang == "de":
            self._re_search_strings = ("Ergebnisse", "von", u"ungefähr")
        elif lang == "es":
            self._re_search_strings = ("Resultados", "de", "aproximadamente")
        # add more localised versions here
        else:
            self._re_search_strings = ("Results", "of", "about")

        if random_agent:
            self.browser.set_random_user_agent()
        
        if mobile:
            self.browser.set_user_mobile_agent()

    @property
    def last_search_url(self):
        return self._last_search_url

    def _get_page(self):
        return self._page

    def _set_page(self, page):
        self._page = page

    page = property(_get_page, _set_page)

    def _get_first_indexed_in_previous(self):
        return self._first_indexed_in_previous

    def _set_first_indexed_in_previous(self, interval):
        if interval == "day":
            self._first_indexed_in_previous = 'd'
        elif interval == "week":
            self._first_indexed_in_previous = 'w'
        elif interval == "month":
            self._first_indexed_in_previous = 'm'
        elif interval == "year":
            self._first_indexed_in_previous = 'y'
        else:
            # a floating point value is a number of months
            try:
                num = float(interval)
            except ValueError:
                raise ScraperError, "Wrong parameter to first_indexed_in_previous: %s" % (str(interval))
            self._first_indexed_in_previous = 'm' + str(interval)
    
    first_indexed_in_previous = property(_get_first_indexed_in_previous, _set_first_indexed_in_previous, doc="possible values: day, week, month, year, or a float value of months")
    
    def _get_filetype(self):
        return self._filetype

    def _set_filetype(self, filetype):
        self._filetype = filetype
    
    filetype = property(_get_filetype, _set_filetype, doc="file extension to search for")
    
    def _get_results_per_page(self):
        return self._results_per_page

    def _set_results_par_page(self, rpp):
        self._results_per_page = rpp

    results_per_page = property(_get_results_per_page, _set_results_par_page)

    def get_results(self):
        """ Gets a page of results """
        if self.eor:
            return []
        MAX_VALUE = 1000000
        startTime = datetime.now()
        page = self._get_results_page()
        runtime = datetime.now() - startTime
        print "Getting Google Search Results in: %f seconds" % (runtime.total_seconds())
        if self.mobile:
            results = self._extract_mobile_results(page)
        else:
            results = self._extract_results(page)
        return results

    def _maybe_raise(self, cls, *arg):
        if self.debug:
            raise cls(*arg)

    def _get_results_page(self):
        if self._page == 0:
            if self._results_per_page == 10:
                url = GoogleScraper.SEARCH_URL_0
            else:
                url = GoogleScraper.SEARCH_URL_1
        else:
            if self._results_per_page == 10:
                url = GoogleScraper.NEXT_PAGE_0
            else:
                url = GoogleScraper.NEXT_PAGE_1

        safe_url = [url % { 'query': urllib.quote_plus(self.query),
                           'start': self._page * self._results_per_page,
                           'num': self._results_per_page,
                           'tld' : self._tld,
                           'lang' : self._lang }]
        
        # possibly extend url with optional properties
        if self._first_indexed_in_previous:
            safe_url.extend(["&as_qdr=", self._first_indexed_in_previous])
        if self._filetype:
            safe_url.extend(["&as_filetype=", self._filetype])
        
        safe_url = "".join(safe_url)
        self._last_search_url = safe_url
        
        try:
            page = self.browser.get_page(safe_url)
        except BrowserError, e:
            raise ScraperError, "Failed getting %s: %s" % (e.url, e.error)
        return page

    def _extract_results(self, page):
        startTime = datetime.now()
        try:
            sel = Selector(text=page)
            titles = sel.xpath(TITLE_XPATH_DESKTOP).extract()
            urls = sel.xpath(URL_XPATH_DESKTOP).extract()
            descs = sel.xpath(DESC_XPATH_DESKTOP).extract()
        except Exception as e:
            print None

        if not titles or not urls or not descs:
            return None       
        cpu_count = multiprocessing.cpu_count()
        contents = self._extract_content_multiprocessing(urls, workers=cpu_count)
        runtime = datetime.now() - startTime
        print "Extracting data in: %f seconds" % (runtime.total_seconds())
        return SearchResult(titles, urls, descs, contents)


    def _extract_mobile_results(self, page):
        startTime = datetime.now()
        try:
            sel = Selector(text=page)
            titles = sel.xpath(TITLE_XPATH_MOBILE).extract()
            urls = sel.xpath(URL_XPATH_MOBILE).extract()
            descs = sel.xpath(DESC_XPATH_MOBILE).extract()
        except Exception as e:
            return None
        
        if not titles or not urls or not descs:
            return None
        cpu_count = multiprocessing.cpu_count()
        contents = self._extract_content_multiprocessing(urls, workers=cpu_count)
        runtime = datetime.now() - startTime
        print "Extracting data in: %f seconds" % (runtime.total_seconds())
        return SearchResult(titles, urls, descs, contents)     
    
    '''# Using ThreadPoolExecutor and boilerpipe
    def _extract_content_threadpoolexecutor(self, urls, workers=10):
        
        def crawl_url(url):
            content = ''
            try:
                extractor = Extractor(extractor='DefaultExtractor', url=url)
                content = extractor.getText()
            except Exception as e:
                pass
            return content
        contents = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_url = {executor.submit(crawl_url, url): url for url in urls}
            for future in as_completed(future_to_url):
                try:
                    content = future.result()
                    contents.append(content)
                except Exception as e:
                    print e
        return contents'''
    
    #Using Process
    def _extract_content_multiprocessing(self, urlresults, workers=4):
        p = Pool(workers)
        sc = Scrapper()
        contents = p.map(sc.crawl_url, urlresults)
        return contents

    def _html_unescape(self, str):
        def entity_replacer(m):
            entity = m.group(1)
            if entity in name2codepoint:
                return unichr(name2codepoint[entity])
            else:
                return m.group(0)

        def ascii_replacer(m):
            cp = int(m.group(1))
            if cp <= 255:
                return unichr(cp)
            else:
                return m.group(0)

        s =    re.sub(r'&#(\d+);',  ascii_replacer, str, re.U)
        return re.sub(r'&([^;]+);', entity_replacer, s, re.U)

class Scrapper(object):
    def crawl_url(self, url):
        content = Content('','')
        try:
            request = urllib2.Request(url)
            page = urllib2.urlopen(request).read()
            if page:
                paragraphs = justext.justext(page, [], stopwords_high=0, stopwords_low = 0, length_low=LENGTH_LOW_DEFAULT)
                text = [para.text for para in paragraphs if not para.is_boilerplate]
                content = Content(url, '\n'.join(text))
        except Exception as e:
            pass   
        return content