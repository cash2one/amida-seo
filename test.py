# -*- coding: utf-8 -*-

from sgoogle.keywordanalyser import KeywordAnalyser

try:
  ka = KeywordAnalyser("Kyoto", numofresults=20, lang="en", tld="com", mobile=False)
  scrapresults = ka.scrap_data()
  print "=========Keyword Extract=============="
  results = ka.extract_keywords(scrapresults.contents, content=True, lang="ja")
  for res in results:
    print "Keyword: %s, score: %s" % (res.word, res.score)
    print
  print "===================================================="
except Exception, e:
  print "Search failed: %s" % e