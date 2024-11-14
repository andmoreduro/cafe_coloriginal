FROM python:3.13-bookworm

RUN apt update -y
RUN apt upgrade -y

RUN pip install --upgrade pip
RUN pip install \
    Django==5.1.3 \
    psycopg==3.2.3 \
    psycopg-binary==3.2.3 \
    uvicorn==0.32.0 \
    uvicorn-worker==0.2.0 \
    phonenumbers==8.13.49 \
    pycountry==24.6.1 \
    babel==2.16.0