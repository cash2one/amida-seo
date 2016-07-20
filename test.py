# -*- coding: utf-8 -*-

from sgoogle.keywordanalyser import KeywordAnalyser

try:
  ka = KeywordAnalyser("京都")
  scrapresults = ka.scrap_data()
  print "=========Keyword Extract=============="
  results = ka.extract_keywords(scrapresults.contents)
  for res in results:
    print "Keyword: %s, score: %s" % (res.word, res.score)
    print
  print "===================================================="
except Exception, e:
  print "Search failed: %s" % e