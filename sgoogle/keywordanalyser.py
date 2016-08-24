# -*- coding: utf-8 -*-
#
# Mai Xuan Trang
#
#
"""
Analyse Google search results and return important keywords
"""

from scraper import GoogleScraper, ScraperError
from alchemyapi import AlchemyAPI
from azureapi import AzureAPI
from yahooapi import YahooAPI
import sys
import justext
import re

ALCHEMY_API_KEY = "27a8e38142c6a48ea64a4c387be8f6da88cb4d1d"
AZURE_API_KEY = "7bcb2e6d08b9421dad41aebadf5761fa"
YAHOO_APP_KEY = "dj0zaiZpPTAxd2RIWGhiWUtyTyZzPWNvbnN1bWVyc2VjcmV0Jng9Y2M-"
KANJI = u'[\u4E00-\u9FFF]+'
HIRA = u'[\u3040-\u309Fー]+'
KATA = u'[\u30A0-\u30FF]+'

class Frequency(object):
    def __init__(self, word, title, frequency):
        self.word = word
        self.title = title
        self.frequency = frequency
    
    def __str__(self):
        return "the word '%s' appears in the title '%s' %s times" % (self.word, self.title, self.frequency)


class Keyword(object):
    def __init__(self, word, score, frequency):
        self.word = word
        self.score = score
        self.frequency = frequency

    def __str__(self):
        return "Keyword word: '%s'. Relevant score: %s" % (self.word, self.score)

    def  __eq__(self, other):
        return self.word == other.word

    def get_score(self):
        return self.score
    
    def  get_pharse(self):
        return self.word

class ScraperResult(object):
    def __init__(self, urls, titles, descriptions, contents):
        self.urls = urls
        self.titles = titles
        self.descriptions = descriptions
        self.contents = contents
    def __str__(self):
        return "Data from scraping %s urls" % len(urls)

class KeywordAnalyser(object):
    def __init__(self, query, numofresults=10, numberofkeywords=50, lang="en", tld="com", mobile=False):

        if mobile:
            random_agent = False
        else:
            random_agent = True

        self.query = query
        self.numberofkeywords = numberofkeywords
        self.scraper = GoogleScraper(query, random_agent=random_agent, debug=True, lang=lang, tld=tld, mobile=mobile)
        self.scraper.results_per_page = numofresults
        self.stoplist = justext.get_stoplist("Japanese")

    def scrap_data(self):
        """Scrap data from google search results"""
        sresults = self.scraper.get_results()
        urls = []
        titles = []
        descriptions = []
        contents = []

        for result in sresults:
            urls.append(result.url)
            titles.append(result.title)
            descriptions.append(result.desc)
            contents.append(result.content)
        
        return ScraperResult(urls,titles,descriptions,contents)
    
    def extract_keyword_en(self, corpus_text, min_len=4, max_len=50):
        alchemyapi = AlchemyAPI(ALCHEMY_API_KEY)

        response = alchemyapi.keywords('text', corpus_text, {'sentiment': 1})

        keywords = []
        if response['status'] == "OK":
            for keyword in response['keywords']:
                phrase = keyword['text'].encode('utf8')
                if phrase.lower() != self.query.lower() and len(phrase) >= min_len and len(phrase) <= max_len:
                    score = float(keyword['relevance'].encode('utf8'))
                    freq = self.phrase_frequency(phrase, corpus_text)
                    kw = Keyword(phrase, score, freq)
                    keywords.append(kw)

        
        return keywords[:min(len(keywords), self.numberofkeywords)]


    #Using Azure API
    def extract_keyword_jp(self, corpus):
        try:
            corpus_text = "\n".join(corpus)
            size = sys.getsizeof(corpus_text)
            if size < 10000:
                keywords = self.get_important_keyphrases_from_single_doc("ja", corpus_text)
            else:
                lines = corpus_text.splitlines()
                noflines = len(lines) / 10
                chunks = [lines[x:x+noflines] for x in range(0, len(lines), noflines)]
                corpus = []
                for chunk in chunks:
                    cor = '\n'.join(chunk)
                    corpus.append(cor)
                keywords = self.get_important_keyphrases_from_multiple_docs("ja", corpus, size, corpus_text)
        except Exception as e:
            raise e
        return keywords
    
    def get_important_keyphrases_from_single_doc(self, lang, corpus_text, min_len=3, max_len=20):
        api = AzureAPI(AZURE_API_KEY)
        keywords = []
        res = api.keyphrases(lang, [corpus_text])
        keyphrases = res["documents"][0]["keyPhrases"]
        for phrase in keyphrases:
            kanjimatch = re.search(KANJI, phrase, re.U)
            hiramatch = re.search(HIRA, phrase, re.U)
            katamatch = re.search(KATA, phrase, re.U)
            if not kanjimatch and not hiramatch and not katamatch:
                continue
            if (len(phrase) >= min_len) and (len(phrase) <= max_len) and (phrase not in self.stoplist) and (phrase.lower() != self.query.lower()):
                score = self.phrase_frequency(phrase, corpus_text)
                kw = Keyword(phrase, score)
                if kw not in keywords:
                    keywords.append(kw)
        return keywords[:min(len(keywords), self.numberofkeywords)]

    def get_important_keyphrases_from_multiple_docs(self, lang, corpus, size, corpus_text, min_len=3, max_len=20):
        api = AzureAPI(AZURE_API_KEY)
        keywords = []
        nofwords = size / 10000
        res = api.keyphrases(lang, corpus)
        docs = res["documents"]
        for doc in docs:
            keyphrases = doc["keyPhrases"]
            for phrase in keyphrases[:nofwords]:
                kanjimatch = re.search(KANJI, phrase, re.U)
                hiramatch = re.search(HIRA, phrase, re.U)
                katamatch = re.search(KATA, phrase, re.U)
                if not kanjimatch and not hiramatch and not katamatch:
                    continue
                if (len(phrase) >= min_len) and (len(phrase) <= max_len) and (phrase not in self.stoplist) and (phrase.lower() != self.query.lower()):
                    score = self.phrase_frequency(phrase, corpus_text)
                    kw = Keyword(phrase, score)
                    if kw not in keywords:
                        keywords.append(kw)
        return keywords

    def extract_keyword_jp_yahoo(self, corpus):
        MAX_DOC_SIZE = 10000
        try:
            corpus_text = "\n".join(corpus)
            size = sys.getsizeof(corpus_text)
            if size < MAX_DOC_SIZE:
                keywords = self.get_important_keyphrases_from_single_doc_yahoo(corpus_text)
            else:
                lines = corpus_text.splitlines()
                nochunks = size / MAX_DOC_SIZE + 1
                noflines = len(lines) / nochunks
                chunks = [lines[x:x+noflines] for x in range(0, len(lines), noflines)]
                docs = []
                for chunk in chunks:
                    cor = '\n'.join(chunk)
                    docs.append(cor)
                keywords = self.get_important_keyphrases_from_multiple_docs_yahoo(docs, corpus_text)
        except Exception as e:
            raise e
        return keywords

    def get_important_keyphrases_from_single_doc_yahoo(self, corpus_text, min_len=3, max_len=20):
        api = YahooAPI(YAHOO_APP_KEY)
        keywords = []
        res = api.keyphrases(corpus_text)
        for phrase, s in res.iteritems():
            kanjimatch = re.search(KANJI, phrase, re.U)
            hiramatch = re.search(HIRA, phrase, re.U)
            katamatch = re.search(KATA, phrase, re.U)
            if not kanjimatch and not hiramatch and not katamatch:
                continue
            if (len(phrase) >= min_len) and (len(phrase) <= max_len) and (phrase not in self.stoplist) and (phrase.lower() != self.query.lower()):
                freq = self.phrase_frequency(phrase, corpus_text)
                kw = Keyword(phrase, float(s)/101, freq)
                if kw not in keywords:
                    keywords.append(kw)
        keywords.sort(key=lambda x: x.score, reverse=True)
        return keywords[:min(len(keywords), self.numberofkeywords)]

    def get_important_keyphrases_from_multiple_docs_yahoo(self, corpus, corpus_text, min_len=3, max_len=20):
        api = YahooAPI(YAHOO_APP_KEY)
        keywords = []

        for cor in corpus:
            res = api.keyphrases(cor)
            for phrase, s in res.iteritems():
                kanjimatch = re.search(KANJI, phrase, re.U)
                hiramatch = re.search(HIRA, phrase, re.U)
                katamatch = re.search(KATA, phrase, re.U)
                if not kanjimatch and not hiramatch and not katamatch:
                    continue
                if (len(phrase) >= min_len) and (len(phrase) <= max_len) and (phrase not in self.stoplist) and (phrase.lower() != self.query.lower()):
                    freq = self.phrase_frequency(phrase, corpus_text)
                    kw = Keyword(phrase, float(s)/101, freq)
                    if kw not in keywords:
                        keywords.append(kw)
        keywords.sort(key=lambda x: x.score, reverse=True)
        return keywords[:min(len(keywords), self.numberofkeywords)]

    def extract_keywords(self, corpus, title=False, des=False, content=False, lang='en'):
        corpus_text = "\n".join(corpus)
        #Todo: Set threshold to filter keywords
        '''threshold = 0
        if title:
            threshold = 0.2
        if des:
            threshold = 0.4
        if content:
            checktext = max(corpus)
        checktext = corpus_text
        alchemyapi = AlchemyAPI(ALCHEMY_API_KEY)
        res = alchemyapi.language('text', checktext)
        lang = ''
        if res['status'] == 'OK':
            lang = res['language']'''
        if lang == "ja":
            return self.extract_keyword_jp_yahoo(corpus)
        else:
            return self.extract_keyword_en(corpus_text)

    def phrase_frequency(self, phrase, text):
        lines = text.lower().splitlines()
        count = 0
        for line in lines:
            ct = line.count(phrase.lower())
            count = count + ct
        return count
    

        
