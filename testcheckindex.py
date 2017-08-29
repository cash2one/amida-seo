# -*- coding: utf-8 -*-

from sgoogle.googleindexchecker import IndexChecker

urls = ['www.hankoyaabc.com/', 'www.vnexpress.net']
checker = IndexChecker(urls, use_proxy=True)
urlchecked = checker.check_solenium()