from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
import requests

# Elasticsearch 연결하기
es = Elasticsearch("http://elasticsearch:9200")


def create_index_if_not_exists():
    """Elasticsearch 인덱스가 없으면 생성"""
    index_name = "research_papers"
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body={
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1
            },
            "mappings": {
                "properties": {
                    "title": { "type": "text" },
                    "abstract": { "type": "text" },
                    "authors": { 
                        "type": "nested",
                        "properties": {
                        "name": { "type": "text" },
                        "institution": { "type": "text" }
                        }
                    },
                    "publication_date": { "type": "date" },
                    "doi": { "type": "keyword" },
                    "category": { "type": "text" },
                    "source": { "type": "keyword" },
                    "url": { "type": "keyword" }
                }
            }
        })
        print(f"Index '{index_name}' has been created.")


def fetch_papers(**kwargs):
    """API를 이용해 논문 데이터 가져오기"""
    url = "https://api.biorxiv.org/covid19/0"
    response = requests.get(url)

    # API 응답 상태 확인
    if response.status_code != 200:
        print(f"API 요청 실패: {response.status_code}")
        return []
    
    papers = response.json().get("collection", [])
    
    # XCom (Cross-Commuinication)을 이용해 데이터 저장하기
    kwargs['ti'].xcom_push(key="papers", value=papers)
    print(f"가져온 논문 데이터 수: {len(papers)}")


def index_papers(**kwargs):
    """Elasticsearch에 논문 색인하기"""
    ti = kwargs['ti']
    papers = ti.xcom_pull(task_ids="fetch_papers", key="papers")

    if not papers:
        print(f"색인할 논문 데이터가 존재하지 않습니다.")
        return
    
    for paper in papers:
        authors_list = [{
            "name": author.get("author_name", "Unknown"),
            "institution": author.get("author_inst", "Unknown")
        } for author in paper.get("rel_authors", [])]
        
        doc = {
            "title": paper.get("rel_title", "No Title"),
            "abstract": paper.get("rel_abs", "No Abstract"),
            "authors": authors_list,
            "publication_date": paper.get("rel_date", "1970-01-01"),
            "doi": paper.get("rel_doi", ""),
            "category": paper.get("category", "Unknown"),
            "source": paper.get("rel_site", "Unknown"),
            "url": paper.get("rel_link", "")
        }

        # 논문 DOI를 Elasticsearch의 _id로 설정해 중복 저장을 방지
        doc_id = paper.get("rel_doi", paper.get("rel_title", "no_id"))

        try:
            es.index(index="research_papers", id=doc_id, body=doc)
            print(f"논문 색인 완료: {doc['title']}")
        except Exception as e:
            print(f"논문 색인 실패 ({doc['title']}): {e}")

# DAG 설정
default_args = {
    "owner": "airflow",
    "start_date": datetime(2025, 2, 4),
    "retries": 1, 
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "paper_etl",
    default_args=default_args,
    schedule_interval="0 6 * * *", # 매일 오전 6시에 실행하도록 설정
    catchup=False
)

init_index_task = PythonOperator(
    task_id="init_es_index",
    python_callable=create_index_if_not_exists,
    dag=dag,
)

fetch_task = PythonOperator(
    task_id="fetch_papers",
    python_callable=fetch_papers,
    provide_context=True,
    dag=dag,
)

index_task = PythonOperator(
    task_id="index_papers",
    python_callable=index_papers,
    provide_context=True,
    dag=dag,
)

init_index_task >> fetch_task >> index_task
