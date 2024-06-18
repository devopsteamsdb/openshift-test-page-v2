FROM python:latest
RUN apt-get update && \
    apt-get install -y fio && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
COPY app.py app/
COPY templates/* app/templates/
WORKDIR /app
RUN pip install Flask
EXPOSE 8080
ENTRYPOINT ["python3", "app.py"]
