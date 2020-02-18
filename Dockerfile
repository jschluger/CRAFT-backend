FROM python:3.7.6-buster

WORKDIR /backend

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . /backend

ENTRYPOINT ["python", "run.py"]