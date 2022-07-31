FROM python:3.10.5-slim-buster

LABEL maintainer="Gorgeous-Ghouls"

## Set env
ENV PYTHONPATH=${PYTHONPATH}:${PWD}
ENV PATH="/root/.local/bin:${PATH}"

## Install pip
RUN apt-get -y update
RUN apt-get -y install git curl
RUN curl -sSL https://install.python-poetry.org | python3 -

RUN mkdir /server
WORKDIR /server
COPY . .

## Install Dependencies
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

EXPOSE 8000

CMD ["poetry", "run","blak-server"]
