# -*- coding: utf-8 -*-

from sgoogle.yahooapi import YahooAPI

api = YahooAPI("dj0zaiZpPTAxd2RIWGhiWUtyTyZzPWNvbnN1bWVyc2VjcmV0Jng9Y2M-")

result = api.keyphrases("東京ミッドタウンから国立新美術館まで歩いて5分で着きます。のリクエストに対するレスポンスです。")

print result