import requests
from bs4 import BeautifulSoup
import random


class ProxyManager:
    def __init__(self, web_proxy_list=["http://54.207.114.172:3333"]):
        self.proxy_list = web_proxy_list
        self.proxy_list += self.freeProxy_url_parser('http://free-proxy-list.net')
        self.proxy_list += self.proxyForEU_url_parser('http://proxyfor.eu/geo.php')
    
    def freeProxy_url_parser(self, web_url):
        curr_proxy_list = []
        content = requests.get(web_url).content
        soup = BeautifulSoup(content, "html.parser")
        table = soup.find("table", attrs={"class": "display fpltable"})

        # The first tr contains the field names.
        headings = [th.get_text() for th in table.find("tr").find_all("th")]

        datasets = []
        for row in table.find_all("tr")[1:10]:
            dataset = zip(headings, (td.get_text() for td in row.find_all("td")))
            datasets.append(dataset)

        for dataset in datasets:
            # Check Field[0] for tags and field[1] for values!
            proxy = "http://"
            for field in dataset:
                if field[0] == 'IP Address':
                    proxy = proxy + field[1] + ':'
                elif field[0] == 'Port':
                    proxy = proxy + field[1]
            curr_proxy_list.append(proxy.__str__())
        return curr_proxy_list
    
    def proxyForEU_url_parser(self, web_url, speed=100.0):
        curr_proxy_list = []
        content = requests.get(web_url).content
        soup = BeautifulSoup(content, "html.parser")
        table = soup.find("table", attrs={"class": "proxy_list"})

        # The first tr contains the field names.
        headings = [th.get_text() for th in table.find("tr").find_all("th")]

        datasets = []
        for row in table.find_all("tr")[1:10]:
            dataset = zip(headings, (td.get_text() for td in row.find_all("td")))
            datasets.append(dataset)

        for dataset in datasets:
            # Check Field[0] for tags and field[1] for values!
            proxy = "http://"
            proxy_straggler = False
            for field in dataset:
                # Discard slow proxies! Speed is in KB/s
                if field[0] == 'Speed':
                    if float(field[1]) < speed:
                        proxy_straggler = True
                if field[0] == 'IP':
                    proxy = proxy + field[1] + ':'
                elif field[0] == 'Port':
                    proxy = proxy + field[1]
            # Avoid Straggler proxies
            if not proxy_straggler:
                curr_proxy_list.append(proxy.__str__())
        return curr_proxy_list

    def get_random_proxy(self):
        random.shuffle(self.proxy_list)
        return random.choice(self.proxy_list)

