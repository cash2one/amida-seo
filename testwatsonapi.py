# -*- coding: utf-8 -*-

import json
from watson_developer_cloud import NaturalLanguageUnderstandingV1
import watson_developer_cloud.natural_language_understanding.features.v1 as Features

nlu = NaturalLanguageUnderstandingV1(username="fe685dda-adb0-4ce5-aac3-1b07a755d0e9", password="RSdlrriH0W0S", version="2017-02-27")

response = nlu.analyze(
    text="Watson Knowledge Studio is a cloud-based application that enables developers and domain experts to collaborate and create custom annotator components for unique industries. These annotators can identify mentions and relationships in unstructured data and be easily administered throughout their lifecycle using one common tool. Annotator components can be deployed directly to IBM Watson Explorer, Watson Natural Language Understanding and Watson Discovery Service.",
    features=[
        Features.Keywords(
        )
    ])

print json.dumps(response, indent=2)
