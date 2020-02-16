FROM python:3.7.6-buster

COPY . /frontend

WORKDIR /frontend

RUN pip3 install -r requirements.txt

ENTRYPOINT ["python", "run.py"]