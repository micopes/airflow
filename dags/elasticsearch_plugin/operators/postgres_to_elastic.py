# 새로운 operator를 만들려고 할 때 baseOperator로부터 상속받아야 한다.
# 모든 operator가 같은 minimum function, attributes을 공유하기 위해서 사용된다.
from airflow.models import BaseOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from elasticsearch_plugin.hooks.elastic_hook import ElasticHook

from contextlib import closing
import json

# BaseOperator를 상속받는다.
class PostgresToElasticOperator(BaseOperator):
    # BaseOperator에서는 *args, **kwargs 인자를 추가 해야 한다.
    def __init__(self, sql, index, 
        postgres_conn_id = "postgres_default", 
        elastic_conn_id = "elasticsearch_default", *args, **kwargs): 

        super(PostgresToElasticOperator, self).__init__(*args, **kwargs)

        self.sql = sql
        self.index = index
        self.postgres_conn_id = postgres_conn_id
        self.elastic_conn_id = elastic_conn_id

    def execute(self, context):
        es = ElasticHook(conn_id = self.elastic_conn_id)
        pg = PostgresHook(postgres_conn_id = self.postgres_conn_id)
        # 연결 및 사용하지 않을 시에는 자동적으로 close할 수 있다.
        with closing(pg.get_conn()) as conn:
            # cursor는 일단 postgres와 상호작용하는 방법이라고 이해하자. realdictcursor 사용(UI에서 Connection 설정), 이 cursor를 이용해서 rows를 json으로 transform
            with closing(conn.cursor()) as cur:
                cur.itersize = 1000
                cur.execute(self.sql)
                for row in cur:
                    doc = json.dumps(row, indent = 2)
                    es.add_doc(index = self.index, doc_type = 'external', doc = doc)

