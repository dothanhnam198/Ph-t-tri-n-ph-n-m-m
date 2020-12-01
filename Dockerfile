FROM python:3
ENV PYTHONUNBUFFERED=1
RUN mkdir /django_app
WORKDIR /E:/Download 2/Django-docker
COPY requirements.txt /django_app/
RUN pip install -r requirements.txt
COPY . /django_app/