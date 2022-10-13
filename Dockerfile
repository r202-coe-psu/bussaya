FROM debian:sid
RUN echo 'deb http://mirror.psu.ac.th/debian/ sid main contrib non-free' > /etc/apt/sources.list
# RUN echo 'deb http://mirror.kku.ac.th/debian/ sid main contrib non-free' >> /etc/apt/sources.list
RUN apt update && apt upgrade -y
RUN apt install -y g++ gcc build-essential python3 python3-dev python3-pip python3-venv ca-certificates git npm

RUN python3 -m venv /venv
ENV PYTHON=/venv/bin/python3
# RUN $PYTHON -m pip install wheel poetry gunicorn
RUN $PYTHON -m pip install wheel poetry uwsgi

WORKDIR /app
COPY poetry.lock pyproject.toml /app/
RUN $PYTHON -m poetry config virtualenvs.create false && $PYTHON -m poetry install --no-interaction --no-dev

COPY bussaya/web/static/package.json bussaya/web/static/package-lock.json bussaya/web/static/
RUN npm install --prefix bussaya/web/static


COPY . /app
ENV BUSSAYA_SETTINGS=/app/bussaya-production.cfg 


EXPOSE 9000
CMD $PYTHON -m uwsgi --lazy-apps --ini scripts/bussaya-uwsgi.ini

