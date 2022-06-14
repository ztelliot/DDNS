FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && \
    apt-get install -y curl iproute2 && \
    rm -rf /var/lib/apt/lists/*

COPY . .

CMD [ "python", "./main.py", "--config", "/config.yaml" ]