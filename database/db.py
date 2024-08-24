from datetime import datetime
from elasticsearch_dsl import Document, Keyword, Text, Nested, Float, Object, Date, Integer
from elasticsearch.helpers import bulk
from elasticsearch_dsl.connections import connections
from elasticsearch import Elasticsearch
import logging


class ElasticsearchConfig:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.es = Elasticsearch("http://localhost:9200")
        self.index_digianalyse = "digianalyse"
        self.index_seo = "seo"
        self.index_domain = "domain"

    def delete_by_query(self, index, body):
        self.es.delete_by_query(index=index, body=body)

class MarketChartDocument(Document):
    user_id = Keyword()
    mention = Text()
    influencer_chart = Nested(
        properties={
            "theme": Text(),
            "documents": Nested(
                properties={
                    "author": Keyword(),
                    "title": Keyword(),
                    "description": Keyword(),
                    "likes": Float(),
                    "source": Keyword()
                }
            )
        }
    )
    leads_chart = Nested(
        properties={
            "interests": Keyword(),
            "texts": Nested(
                properties={
                    "author": Keyword(),
                    "text": Text(),
                    "source": Keyword()
                }
            )
        }
    )

class SeoChartDocument(Document):
    user_id = Keyword()
    timestamp = Date() 
    topics_chart = Nested(
        properties={
            "topics": Keyword(multi=True),
            "counts": Object(), 
            "hashtags": Object(),
            "wordclouds": Object()
        }
    )

class DomainChartDocument(Document):
    domain = Keyword()
    timestamp = Date()
    domain_chart = Nested(
        properties={
            "domains": Keyword(multi=True),
            "da_scores_percentages": Integer(multi=True),
            "pa_scores_percentages": Integer(multi=True),
            "spam_scores": Float(multi=True),
            "total_backlinks": Integer(multi=True),
            "colors": Keyword(multi=True), 
            "clusters": Integer(multi=True) 
        }
    )

def find_insert_or_delete_market_charts(index_digianalyse, influencer,  leads, mention):
    new_documents = []
    new_document = MarketChartDocument(
        user_id="123456789",
        mention=mention,
        influencer_chart=influencer,
        leads_chart=leads
    )
    
    new_documents.append(new_document.to_dict(True))
    
    bulk(
        connections.get_connection(),
        actions=new_documents,
        index=index_digianalyse)
    
#{"settings":{"number_of_shards":2,"number_of_replicas":1},"mappings":{"dynamic":false,"properties":{"user_id":{"type":"keyword"},"mention":{"type":"text"},"influencer_chart":{"properties":{"theme":{"type":"text"},"documents":{"type":"nested","properties":{"author":{"type":"keyword"},"title":{"type":"text"},"description":{"type":"text"},"likes":{"type":"double"},"source":{"type":"keyword"}}}}},"leads_chart":{"properties":{"interests":{"type":"text"},"texts":{"type":"nested","properties":{"author":{"type":"keyword"},"source":{"type":"keyword"},"text":{"type":"keyword"}}}}}}}}
    
def find_insert_or_delete_topics_charts(index_seo, topics_chart):
    new_documents = []
    new_document = SeoChartDocument(
        user_id="123456789",
        timestamp=datetime.now(),
        topics_chart=topics_chart
    )
    
    new_documents.append(new_document.to_dict(True))
    
    bulk(
        connections.get_connection(),
        actions=new_documents,
        index=index_seo)

# {
#   "settings": {
#     "number_of_shards": 2,
#     "number_of_replicas": 1
#   },
#   "mappings": {
#     "properties": {
#       "user_id": {
#         "type": "keyword"
#       },
#       "timestamp": {
#         "type": "date"
#       },
#       "topics_chart": {
#         "properties": {
#           "topics": {
#             "type": "keyword"
#           },
#           "counts": {
#             "type": "object"
#           },
#           "hashtags": {
#             "type": "object"
#           },
#           "wordclouds": {
#             "type": "object"
#           }
#         }
#       }
#     }
#   }
# }


def find_insert_or_delete_domain_charts(index_domain, domain, domain_chart):
    new_documents = []
    new_document = DomainChartDocument(
        domain=domain,
        timestamp=datetime.now(),
        domain_chart=domain_chart
    )
    
    new_documents.append(new_document.to_dict(True))
    
    bulk(
        connections.get_connection(),
        actions=new_documents,
        index=index_domain)
    

# {
#   "settings": {
#     "number_of_shards": 2,
#     "number_of_replicas": 1
#   },
#   "mappings": {
#     "properties": {
#       "domain": {
#         "type": "keyword"
#       },
#       "timestamp": {
#         "type": "date"
#       },
#       "domain_chart": {
#         "properties": {
#           "domains": {
#             "type": "keyword"
#           },
#           "da_scores_percentages": {
#             "type": "integer"
#           },
#           "pa_scores_percentages": {
#             "type": "integer"
#           },
#           "spam_scores": {
#             "type": "float"
#           },
#           "total_backlinks": {
#             "type": "long"
#           },
#           "colors": {
#             "type": "keyword"
#           },
#           "clusters": {
#             "type": "integer"
#           }
#         }
#       }
#     }
#   }
# }
