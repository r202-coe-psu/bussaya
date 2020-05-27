FROM debian:sid
RUN echo 'deb http://mirrors.psu.ac.th/debian/ sid main contrib non-free' > /etc/apt/sources.list
# RUN echo 'deb http://mirror.kku.ac.th/debian/ sid main contrib non-free' >> /etc/apt/sources.list
RUN apt update && apt upgrade -y
RUN apt install -y g++ gcc build-essential python3 python3-dev python3-pip python3-venv ca-certificates

COPY . /app
WORKDIR /app
RUN pip3 install flask uwsgi; pip3 install -e git+https://github.com/authlib/loginpass#egg=loginpass
RUN python3 setup.py develop
ENV BUSSAYA_SETTINGS=/app/bussaya-production.cfg
ENV FLASK_ENV=prodoction
ENV AUTHLIB_INSECURE_TRANSPORT=true


EXPOSE 9001
CMD scripts/bussaya-uwsgi.sh

