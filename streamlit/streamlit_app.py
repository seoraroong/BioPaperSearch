import streamlit as st
import requests

# FastAPI 백엔드 URL (컨테이너 네트워크에서 FastAPI와 통신하기 위함)
BACKEND_URL = "http://fastapi:8000/search"

st.title("📚 BioResearch-Paper Search Engine")
st.write("Elasticsearch 기반 bio 논문 검색")

# 검색 입력창
query = st.text_input("검색어를 입력하세요", "")

# 저자 검색 옵션
author = st.text_input("저자 이름을 입력하세요", "")

# 검색 버튼
if st.button("검색"):
    params = {"query": query}
    if author:
        params["author"] = author
    
    response = requests.get(BACKEND_URL, params=params)

    if response.status_code == 200:
        results = response.json().get("results", [])
        if results:
            st.write(f"🔍 {len(results)}개의 논문이 검색되었습니다.")
            for paper in results:
                source = paper["_source"]
                st.subheader(source["title"])
                st.write(f"**저자:** {', '.join([author['name'] for author in source['authors']])}")
                st.write(f"📅 **출판일:** {source['publication_date']}")
                st.write(f"📖 **요약:** {source['abstract'][:500]}...")
                st.write(f"[🔗 논문 링크]({source['url']})")
                st.write("---")
        else:
            st.warning("검색 결과가 없습니다")
    else:
        st.error("검색 요청에 실패했습니다")