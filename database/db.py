from elasticsearch_dsl import Document, Keyword, Text, Nested, Float, Integer
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
        self.index_market = "market"

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


def find_insert_or_delete_market_charts(index_digianalyse, charts, mention):
    new_documents = []
    new_document = MarketChartDocument(
        user_id=charts.get("user_id"),
        mention=mention,
        influencer_chart=charts.get("influencer_chart"),
        leads_chart=charts.get("leads_chart")
    )
    
    new_documents.append(new_document.to_dict(True))
    
    bulk(
        connections.get_connection(),
        actions=new_documents,
        index=index_digianalyse)
    return charts
