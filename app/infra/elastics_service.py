from elasticsearch import Elasticsearch

es = Elasticsearch(["http://localhost:9200"])

def index_product(product_id: int, product_data: dict):
    es.index(index="products", id=product_id, body=product_data)
