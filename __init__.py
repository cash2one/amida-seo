# -*- coding: utf-8 -*-
#
# Mai Xuan Trang
# Flask application
#
import os
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from sgoogle.keywordanalyser import KeywordAnalyser
from datetime import datetime
import sys
from pymongo import MongoClient
import jsonpickle

reload(sys)  
sys.setdefaultencoding('utf8')

#configuration
MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017
MONGODB_DB = 'amida_seo'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

client = MongoClient(app.config['MONGODB_HOST'], app.config['MONGODB_PORT'])

@app.route('/')
def show_entries():
    return render_template('show_entries.html', selectedst='ds', selectedcountry='co.jp')

@app.route('/', methods=['POST'])
def show_result():
    searchtype = request.form['searchtype'].encode('utf8')
    country = request.form['country']
    if country == 'com':
        language = 'en'
    elif country == 'co.jp':
        language = 'ja'
    mobile = False
    if searchtype == 'ms':
        mobile = True
    
    keyword = request.form['keyword'].encode('utf8')

    if keyword == '':
        return render_template('show_entries.html', keyword=keyword, selectedcountry=country, selectedst=searchtype, error="You did not enter a keyword!")
    else:
        db = client[app.config[('MONGODB_DB')]]
        coll = db.relevant_keywords
        keyword_exist = coll.find_one({"keyword":keyword, "searchtype":searchtype})
        if keyword_exist:
            content_keywords = jsonpickle.decode(keyword_exist['content_keywords'])
            title_keywords = None
            des_keywords = None
            return render_template('show_entries.html', keyword=keyword, selectedcountry=country, title_keywords=title_keywords, des_keywords=des_keywords, content_keywords=content_keywords, selectedst=searchtype)
        else:
            try:
                startTime0 = datetime.now()
                analyser = KeywordAnalyser(keyword, numofresults=30, lang=language, tld=country, mobile=mobile)
                scrapresult = analyser.scrap_data();
                startTime1 = datetime.now()
                title_keywords = None#analyser.extract_keywords(scrapresult.titles, lang=language)
                des_keywords = None#analyser.extract_keywords(scrapresult.descs, lang=language)
                content_keywords = analyser.extract_keywords(scrapresult.contents, content=True, lang=language)
                print "Extracting Keywords in: %f" %((datetime.now() - startTime1).total_seconds())
                print "Total processing time: %f" %((datetime.now() - startTime0).total_seconds())

                re_keywords = {"keyword":keyword, "searchtype":searchtype, "content_keywords":jsonpickle.encode(content_keywords)}
                coll.insert(re_keywords)

                return render_template('show_entries.html', keyword=keyword, selectedcountry=country, title_keywords=title_keywords, des_keywords=des_keywords, content_keywords=content_keywords, selectedst=searchtype)
            except Exception, e:
                return render_template('show_entries.html', keyword=keyword, selectedcountry=country, selectedst=searchtype, error=e)

if __name__ == "__main__":
	app.run()