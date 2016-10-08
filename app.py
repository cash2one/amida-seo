# -*- coding: utf-8 -*-
#
# Mai Xuan Trang
# Flask application
#
import os
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from sgoogle.keywordanalyser import KeywordAnalyser
from sgoogle.googleindexchecker import IndexChecker
from datetime import datetime
import sys
from pymongo import MongoClient
import jsonpickle
import os
from werkzeug.utils import secure_filename

reload(sys)  
sys.setdefaultencoding('utf8')

#configuration
MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017
MONGODB_DB = 'amida_seo'

UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = set(['txt'])

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
        keyword_exist = coll.find_one({"keyword":keyword, "searchtype":searchtype, "country":country})
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

                re_keywords = {"keyword":keyword, "searchtype":searchtype, "country":country, "content_keywords":jsonpickle.encode(content_keywords)}
                coll.insert(re_keywords)

                return render_template('show_entries.html', keyword=keyword, selectedcountry=country, title_keywords=title_keywords, des_keywords=des_keywords, content_keywords=content_keywords, selectedst=searchtype)
            except Exception, e:
                return render_template('show_entries.html', keyword=keyword, selectedcountry=country, selectedst=searchtype, error=e)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/googleindexchecker')
def show_index_checker():
    return render_template('index_check.html')


@app.route('/googleindexchecker', methods=['POST'])
def check_result():
    file = request.files['file']
    if file.filename == '':
        return render_template('index_check.html', error='No selected file')
    
    if not allowed_file(file.filename):
        return render_template('index_check.html', error='File type is not supported')
    
    if file and allowed_file(file.filename):
        urlstr = file.read()
        urls = urlstr.split()
        checker = IndexChecker(urls, tld="co.jp")
        urlchecked = checker.check()
        return render_template('index_check.html', urlindexchecks=urlchecked)



if __name__ == "__main__":
	app.run()