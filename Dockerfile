FROM debian:sid
RUN echo 'deb http://mirror.psu.ac.th/debian/ sid main contrib non-free' > /etc/apt/sources.list
# RUN echo 'deb http://mirror.kku.ac.th/debian/ sid main contrib non-free' >> /etc/apt/sources.list
RUN apt update && apt upgrade -y
RUN apt install -y g++ gcc build-essential python3 python3-dev python3-pip python3-venv ca-certificates git npm locales

RUN sed -i '/th_TH.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG th_TH.UTF-8 
ENV LANGUAGE th_TH:en

RUN python3 -m venv /venv
ENV PYTHON=/venv/bin/python3
# RUN $PYTHON -m pip install wheel poetry gunicorn
RUN $PYTHON -m pip install wheel poetry gunicorn

WORKDIR /app
COPY poetry.lock poetry.toml pyproject.toml README.md /app/
RUN . /venv/bin/activate \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --only main --no-root

COPY bussaya/web/static/package.json bussaya/web/static/package-lock.json bussaya/web/static/
RUN npm install --prefix bussaya/web/static


COPY . /app
ENV BUSSAYA_SETTINGS=/app/bussaya-production.cfg 


