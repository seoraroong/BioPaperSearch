from fastapi import FastAPI, Query
from elasticsearch import Elasticsearch

app = FastAPI()
es = Elasticsearch("http://elasticsearch:9200")

@app.get("/search")
async def search_papers(
    query: str = Query(None, description="Search by keyword"),
    author: str = Query(None, description="Search by author's name"),
    sort_by: str = Query("publication_date", description="Sort field"),
    order: str = Query("desc", description="Sort order ('asc' or 'desc')")
):
    """Elasticsearch에서 논문 검색 수행"""

    must_clauses = []

    # 키워드 검색 추가 (query가 존재하는 경우)
    if query:
        must_clauses.append(
            {"multi_match": {
                "query": query,
                "fields": ["title", "abstract", "category"]
            }}
        )

    # 저자 검색 추가 (author가 존재하는 경우)
    if author:
        must_clauses.append(
            {
                "nested": {
                    "path": "authors",
                    "query": {
                        "match": {
                            "authors.name": author
                        }
                    }
                }
            }
        )

    # 검색어 또는 저자 중 하나는 반드시 입력해야 함
    if not must_clauses:
        return {"error": "검색어 또는 저자를 입력해야 합니다."}

    query_body = {
        "query": {
            "bool": {
                "must": must_clauses
            }
        },
        "sort": [
            {sort_by: {"order": order}}
        ]
    }

    response = es.search(index="research_papers", body=query_body)

    return {"results": response["hits"]["hits"]}


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}