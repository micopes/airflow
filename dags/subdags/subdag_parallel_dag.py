from airflow import DAG
from airflow.operators.bash import BashOperator

# default_args는 with DAG의 parameter인 default_args와 같아야 한다.
def subdag_parallel_dag(parent_dag_id, child_dag_id, default_args):
    with DAG(dag_id = f'{parent_dag_id}.{child_dag_id}', default_args = default_args) as dag:


        return dag