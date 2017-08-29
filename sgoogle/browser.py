#!/usr/bin/python
#
# Mai Xuan Trang
#

import random
import socket
import urllib
import urllib2
import httplib
from userAgent import UserAgentManager
from proxy import ProxyManager
import requests

import ssl

MOBILES = (
    'Mozilla/5.0 (iPhone; CPU iPhone OS 9_3 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13E188a Safari/601.1',
    'Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Mobile Safari/535.19',
    'Mozilla/5.0 (iPad; CPU OS 9_3 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13E188a Safari/601.1'
)

TIMEOUT = 600  # socket timeout

class BrowserError(Exception):
    def __init__(self, url, error):
        self.url = url
        self.error = error

class PoolHTTPConnection(httplib.HTTPConnection):
    def connect(self):
        """Connect to the host and port specified in __init__."""
        msg = "getaddrinfo returns an empty list"
        for res in socket.getaddrinfo(self.host, self.port, 0,
                                      socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                self.sock = socket.socket(af, socktype, proto)
                if self.debuglevel > 0:
                    print "connect: (%s, %s)" % (self.host, self.port)
                self.sock.settimeout(TIMEOUT)
                self.sock.connect(sa)
            except socket.error, msg:
                if self.debuglevel > 0:
                    print 'connect fail:', (self.host, self.port)
                if self.sock:
                    self.sock.close()
                self.sock = None
                continue
            break
        if not self.sock:
            raise socket.error, msg

class PoolHTTPHandler(urllib2.HTTPHandler):
    def http_open(self, req):
        return self.do_open(PoolHTTPConnection, req)

class Browser(object):
    def __init__(self, web_proxy_list=[], use_proxy=False):
        self.userAgent = UserAgentManager()
        self.use_proxy = use_proxy
        self.headers = {
            'User-Agent': self.userAgent.get_first_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5'
        }

    def set_user_mobile_agent(self):
        self.headers['User-Agent'] = MOBILES[0]
        return self.headers['User-Agent']

    def set_random_user_agent(self):
        self.headers['User-Agent'] = self.userAgent.get_random_user_agent()
        return self.headers['User-Agent']


    def get_page(self, url, data=None):
        if self.use_proxy:
            #proxy = ProxyManager()
            proxies = {
                'http':'http://127.0.0.1:8123'
            }
            try:
                data = requests.get(url, headers=self.headers, proxies=proxies)
                return data.content
            except Exception as e:
                raise BrowserError(url, str(e))
        else:
            handlers = [PoolHTTPHandler]
            opener = urllib2.build_opener(*handlers)
            if data: data = urllib.urlencode(data)
            request = urllib2.Request(url, data, self.headers)
            try:
                #response = urllib2.urlopen(request)
                response = opener.open(request)
                '''sslcontext = ssl._create_unverified_context()
                response = urllib2.urlopen(request, context=sslcontext)'''
                return response.read()
            except (urllib2.HTTPError, urllib2.URLError), e:
                raise BrowserError(url, str(e))
            except (socket.error, socket.sslerror), msg:
                raise BrowserError(url, msg)
            except socket.timeout, e:
                raise BrowserError(url, "timeout")
            except KeyboardInterrupt:
                raise
            except:
                raise BrowserError(url, "unknown error")