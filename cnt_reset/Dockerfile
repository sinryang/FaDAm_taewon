FROM python:3.7

WORKDIR /cnt_reset

COPY . /cnt_reset


RUN pip3 install configparser==3.7.3
RUN pip3 install psycopg2==2.7.7
RUN pip3 install psycopg2-binary==2.7.7
RUN pip3 install tornado==6.0.1

CMD ["python3", "cnt_reset.py"]
