FROM python:alpine3.7
RUN apk add gcc musl-dev python3-dev libffi-dev openssl-dev tzdata
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 5000
CMD flask run --host=0.0.0.0 --port=5000