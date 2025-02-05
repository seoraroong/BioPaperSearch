FROM apache/airflow:2.7.3

USER root

WORKDIR /opt/airflow

RUN apt update && apt install -y procps sudo

USER airflow

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Airflow 초기화
CMD ["bash", "-c", "airflow db migrate && airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com && airflow scheduler & airflow webserver"]
