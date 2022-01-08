FROM python:3.9-alpine3.15
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY ./requirement.txt /code/
RUN apt update
RUN apt -y upgrade
RUN apt install -y libreoffice
RUN apt-get install libmagic1
RUN pip3 install -r requirement.txt
COPY . /code/

EXPOSE 8000
CMD ["python", "app.py"]
