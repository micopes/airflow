# Import DAG object - 데이터 파이프라인 생성 시 사용
from airflow.models import DAG
# SQlite operator 사용 가능, sqlite DB와 interact
from airflow.providers.sqlite.operators.sqlite import SqliteOperator
# HTTP Sensor 사용해서 API가 동작 중인지 여부를 파악
from airflow.providers.http.sensors.http import HttpSensor
# fetch the result of a given page of a given url
from airflow.providers.http.operators.http import SimpleHttpOperator
# table에 저장하기를 원하는 user정보를 extract하기 위해서 사용
from airflow.operators.python import PythonOperator
# 앞서 extract한 정보를 sqlite에 저장하기 위해서 사용
from airflow.operators.bash import BashOperator


from datetime import datetime
from pandas import json_normalize
import json

def _processing_user(ti):
    users = ti.xcom_pull(task_ids = ['extracting_user'])
    # output empty / output이 예상한 것이 아닌 경우(results가 안들어있는 경우)
    if not len(users) or 'results' not in users[0]:
        raise ValueError('User is empty')
    user = users[0]['results'][0] # json 읽어오기
    processed_user = json_normalize({
        'firstname': user['name']['first'],
        'lastname': user['name']['last'],
        'country': user['location']['country'],
        'username': user['login']['username'],
        'password': user['login']['password'],
        'email': user['email']
    })
    processed_user.to_csv('/tmp/processed_user.csv', index = None, header = False)

# 딕셔너리에서 specify argument 설정(default) (ex) retry 횟수)
default_args = {
    'start_date': datetime(2020, 1, 1)
}

# instanciate DAG object, (DAG ID(unique), trigger 주기, 시작 날짜, catchup
'''
with DAG('user_processing', schedule_interval = '@daily', 
        start_date = datetime(2020, 1, 1), 
        catchup = False) as dag:
'''
with DAG('user_processing', schedule_interval = '@daily', 
        default_args = default_args,
        catchup = True) as dag:
    
    creating_table = SqliteOperator(
        # unique ID 
        task_id = 'creating_table',
        sqlite_conn_id = 'db_sqlite',
        sql = '''
              CREATE TABLE if not exists users (
                  firstname TEXT NOT NULL,
                  lastname TEXT NOT NULL,
                  country TEXT NOT NULL,
                  username TEXT NOT NULL,
                  password TEXT NOT NULL,
                  email TEXT NOT NULL PRIMARY KEY
              );
              '''
    )

    # HTTP에 의해 URL API가 Checked
    # 앞에 user_api conn Id의 Host가 "https://randomuser.me/" 이므로 endpoint 'api/를 받으면
    # "http://randomuser.me/api/" 가 된다.
    is_api_available = HttpSensor(
        task_id = 'is_api_available',
        http_conn_id = 'user_api',
        endpoint = 'api/'
    )

    extracting_user = SimpleHttpOperator(
        task_id = 'extracting_user',
        http_conn_id = 'user_api',
        endpoint = 'api/',
        # 데이터의 변경을 하는 것이 아니라 가져오기만 하기 때문에
        method = 'GET',
        # response를 처리할 수 있도록 허락
        response_filter = lambda response : json.loads(response.text),
        # URL의 response를 확인할 수 있다.
        log_response = True
    )

    processing_user = PythonOperator(
        task_id = 'processing_user',
        # python operator로부터 호출하고 싶은 operator
        python_callable = _processing_user
    )

    storing_user = BashOperator(
        task_id = 'storing_user',
        # ','로 분리, 해당 파일의 users를 import해서 airflow의 sqlite에 저장.
        bash_command = 'echo -e ".separator ","\n.import /tmp/processed_user.csv users" | sqlite3 /home/airflow/airflow/airflow.db'
    )

    # Dependency
    creating_table >> is_api_available >> extracting_user >> processing_user >> storing_user




