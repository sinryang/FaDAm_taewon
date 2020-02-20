FROM python:3.7

WORKDIR /web

COPY . /web


RUN pip3 install configparser==3.7.3
RUN pip3 install psycopg2==2.7.7
RUN pip3 install psycopg2-binary==2.7.7
RUN pip3 install tornado==6.0.1

EXPOSE 8888

CMD ["python3", "web.py"]
