FROM python:3.12-slim
RUN apt-get update && \
    apt-get install -y fio && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install Flask

COPY app.py .
COPY templates/ templates/

EXPOSE 8080
ENTRYPOINT ["python3", "app.py"]
