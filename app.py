# -*- coding: utf-8 -*-
#
# Mai Xuan Trang
# Flask application
#
import os
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from sgoogle.keywordanalyser import KeywordAnalyser
import sys  

reload(sys)  
sys.setdefaultencoding('utf8')

#configuration
MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017
MONGODB_DB = 'amida_seo'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

@app.route('/')
def show_entries():
    return render_template('show_entries.html', selectedst='ds')

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
        return render_template('show_entries.html', error="You did not enter a keyword!")
    else:
        try:
            analyser = KeywordAnalyser(keyword, numofresults=30, lang=language, tld=country, mobile=mobile)
            scrapresult = analyser.scrap_data();
            title_keywords = analyser.extract_keywords(scrapresult.titles, lang=language)
            des_keywords = analyser.extract_keywords(scrapresult.descs, lang=language)
            content_keywords = analyser.extract_keywords(scrapresult.contents, content=True, lang=language)
            return render_template('show_entries.html', keyword=keyword, selectedcountry=country, title_keywords=title_keywords, des_keywords=des_keywords, content_keywords=content_keywords, selectedst=searchtype)
        except Exception, e:
            return render_template('show_entries.html', keyword=keyword, selectedcountry=country, error=e)