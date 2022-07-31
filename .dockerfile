FROM python:3.10.0

LABEL maintainer="Gorgeous-Ghouls"

RUN pip install poetry

RUN git clone https://github.com/Gorgeous-Ghouls/Blak.git /home/Blak

WORKDIR /home/Blak/server
RUN poetry install

EXPOSE 8000

CMD ["poetry", "run","blak-server"]
