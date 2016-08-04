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

# create our little application :)
app = Flask(__name__)

@app.route('/')
def show_entries():
    return render_template('show_entries.html')

@app.route('/', methods=['POST'])
def show_result():
    #engine = request.form['engine'].encode('utf8')
    keyword = request.form['keyword'].encode('utf8')
    country = request.form['country']

    analyser = KeywordAnalyser(keyword, tld=country);
    """if keyword == 'debug':
        return render_template('show_entries.html', error=engine)"""
    if keyword == '':
        return render_template('show_entries.html', error="You did not enter a keyword!")
    else:
        try:
            scrapresult = analyser.scrap_data();
            title_keywords = analyser.extract_keywords(scrapresult.titles)
            des_keywords = analyser.extract_keywords(scrapresult.descriptions)
            content_keywords = analyser.extract_keywords(scrapresult.contents)
            return render_template('show_entries.html', keyword=keyword, selectedcountry=country,title_keywords=title_keywords, des_keywords=des_keywords, content_keywords=content_keywords)
        except Exception, e:
            return render_template('show_entries.html', keyword=keyword, selectedcountry=country, error=e)

if __name__ == "__main__":
	app.run()