FROM python:3.10.15-slim

WORKDIR /app

RUN apt-get update
RUN apt-get -y install locales && \
    localedef -f UTF-8 -i ja_JP ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ JST-9
ENV TERM xterm

RUN apt-get install -y vim less
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools



COPY . .

RUN pip install .

# Streamlit が使用するポートを開放
EXPOSE 8501

# healthcheck を追加
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Streamlit を実行
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]