# 모든 hook에 사용, 최소한의 속성, 메소드를 공유하기 위해서.
from airflow.hooks.base import BaseHook

from elasticsearch import Elasticsearch

class ElasticHook(BaseHook):
    def __init__(self, conn_id = 'elasticsearch_default', *args, **kwargs):
        super().__init__(*args, **kwargs)
        conn = self.get_connection(conn_id)

        conn_config = {}
        hosts = [] # elasticsearch가 multiple machine에 일치하는 multiple hosts를 가질 수 있다.

        if conn.host:
            hosts = conn.host.split(',')
        if conn.port:
            conn_config['port'] = int(conn.port)
        if conn.login:
            conn_config['http_auth'] = (conn.login, conn.password)

        # 위의 conn_id, host, port, login 의 설정으로 elasticsearch를 init
        self.es = Elasticsearch(hosts, **conn_config) 
        self.index = conn.schema

    def info(self):
        return self.es.info()
    
    def set_index(self, index):
        self.index = index
    
    # data 저장
    def add_doc(self, index, doc_type, doc):
        self.set_index(index)
        res = self.es.index(index = index, doc_type = doc_type, body = doc)
        return res
    
    