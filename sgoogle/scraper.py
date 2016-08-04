#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
# Mai Xuan Trang
# 
#

import re
import urllib
from htmlentitydefs import name2codepoint
from BeautifulSoup import BeautifulSoup

from browser import Browser, BrowserError

from alchemyapi import AlchemyAPI

import justext

import sys  

reload(sys)  
sys.setdefaultencoding('utf8')

LENGTH_LOW_DEFAULT = 100

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
    def __init__(self, title, url, desc, content):
        self.title = title
        self.url = url
        self.desc = desc
        self.content = content

    def __str__(self):
        return 'Google Search Result: "%s"' % self.title

class GoogleScraper(object):
    SEARCH_URL_0 = "http://www.google.%(tld)s/search?hl=%(lang)s&q=%(query)s&btnG=Google+Search"
    NEXT_PAGE_0 = "http://www.google.%(tld)s/search?hl=%(lang)s&q=%(query)s&start=%(start)d"
    SEARCH_URL_1 = "http://www.google.%(tld)s/search?hl=%(lang)s&q=%(query)s&num=%(num)d&btnG=Google+Search"
    NEXT_PAGE_1 = "http://www.google.%(tld)s/search?hl=%(lang)s&q=%(query)s&num=%(num)d&start=%(start)d"

    def __init__(self, query, random_agent=False, debug=False, lang="en", tld="com", re_search_strings=None):
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

    @property
    def num_results(self):
        if not self.results_info:
            page = self._get_results_page()
            self.results_info = self._extract_info(page)
            if self.results_info['total'] == 0:
                self.eor = True
        return self.results_info['total']

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
        page = self._get_results_page()
        #search_info = self._extract_info(page)
        results = self._extract_results(page)
        search_info = {'from': self.results_per_page*self._page,
                       'to': self.results_per_page*self._page + len(results),
                       'total': MAX_VALUE}
        if not self.results_info:
            self.results_info = search_info
            if self.num_results == 0:
                self.eor = True
                return []
        if not results:
            self.eor = True
            return []
        if self._page > 0 and search_info['from'] == self._last_from:
            self.eor = True
            return []
        if search_info['to'] == search_info['total']:
            self.eor = True
        self._page += 1
        self._last_from = search_info['from']
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

        return BeautifulSoup(page)

    def _extract_info(self, soup):
        empty_info = {'from': 0, 'to': 0, 'total': 0}
        div_ssb = soup.find('div', id='ssb')
        if not div_ssb:
            self._maybe_raise(ParseError, "Div with number of results was not found on Google search page", soup)
            return empty_info
        p = div_ssb.find('p')
        if not p:
            self._maybe_raise(ParseError, """<p> tag within <div id="ssb"> was not found on Google search page""", soup)
            return empty_info
        txt = ''.join(p.findAll(text=True))
        txt = txt.replace(',', '')
        matches = re.search(r'%s (\d+) %s\s+\((\d+\.\d+) %s\)' % self._re_search_strings, txt, re.U)
        if not matches:
            return empty_info
        return {'from': int(matches.group(1)), 'to': int(matches.group(2)), 'total': int(matches.group(3))}

    def _extract_results(self, soup):
        results = soup.findAll('div', {'class': 'g'})
        ret_res = []
        for result in results:
            if(result.find('span', {'class': 'st'})):
                eres = self._extract_result(result)
                if eres:
                    ret_res.append(eres)
        return ret_res

    def _extract_result(self, result):
        title, url = self._extract_title_url(result)
        desc = self._extract_description(result)
        
        if not title or not url or not desc:
            return None
        content = self._extract_content(url)
        return SearchResult(title, url, desc, content)

    def _extract_title_url(self, result):
        #title_a = result.find('a', {'class': re.compile(r'\bl\b')})
        title_h = result.find('h3', {'class':'r'})
        if not title_h:
            self._maybe_raise(ParseError, "Title tag in Google search result was not found", result)
            return None, None
        title_a = title_h.find('a')
        title = ''.join(title_a.findAll(text=True))
        title = self._html_unescape(title)
        url = title_a['href']
        match = re.match(r'/url\?q=(http[^&]+)&', url)
        if not match:
            return None, None
        else:
            url = urllib.unquote(match.group(1))
        return title, url

    def _extract_description(self, result):
        desc_span = result.find('span', {'class': 'st'})
        if not desc_span:
            self._maybe_raise(ParseError, "Description tag in Google search result was not found", result)
            return None
        desc = ''.join(desc_span.findAll(text=True))
        return self._html_unescape(desc)

    # Extract content with AlchemyAPI
    def _extract_content_alchemy(self, url):
        alchemyapi = AlchemyAPI()
        response = alchemyapi.text('url', url)
        content = ''
        if response['status'] == 'OK':
            content = response['text']
        return content

    
    def _extract_content(self, url):
        scraper = WebContentScraper(url, min_len=100, random_agent=True, debug=True)
        return scraper._extract_content()
    
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

class WebContentScraper(GoogleScraper):

    def __init__(self, url, random_agent=False, debug=False, min_len=LENGTH_LOW_DEFAULT):
        self.url = url
        self.debug = debug
        self.min_len = min_len
        self.browser = Browser(debug=debug)

    def _extract_content(self):
        try:
            page = self.browser.get_page(self.url)
        except BrowserError, e:
            #raise ScraperError, "Failed to crawl website '%s': %s" %(self.url, e.error)
            return ''
        
        paragraphs = justext.justext(page, [], stopwords_high=0, stopwords_low = 0, length_low=self.min_len)
        text = []
        if len(paragraphs) < 1:
            return "Justext failed"
        for paragraph in paragraphs:
            if not paragraph.is_boilerplate:
                text.append(paragraph.text)
                
        content = '\n'.join(text)
        return content

        
