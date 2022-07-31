FROM debian:sid
RUN echo 'deb http://mirror.psu.ac.th/debian/ sid main contrib non-free' > /etc/apt/sources.list
# RUN echo 'deb http://mirror.kku.ac.th/debian/ sid main contrib non-free' >> /etc/apt/sources.list
RUN apt update && apt upgrade -y
RUN apt install -y g++ gcc build-essential python3 python3-dev python3-pip python3-venv ca-certificates git npm

COPY . /app
WORKDIR /app
RUN pip3 install flask uwsgi
RUN npm install --prefix bussaya/static

ENV BUSSAYA_SETTINGS=/app/bussaya-production.cfg 
ENV FLASK_ENV=prodoction 
ENV AUTHLIB_INSECURE_TRANSPORT=true
ENV PYTHONPATH=$(pwd):/usr/lib/python3.10/site-packages:$PYTHONPATH

RUN pip3 install poetry uwsgi
RUN poetry config virtualenvs.create false && poetry install --no-interaction


EXPOSE 9001
CMD scripts/bussaya-uwsgi.sh

