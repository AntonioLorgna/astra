FROM python:3.10.9-slim

# set env variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"


RUN --mount=type=cache,target=/root/.cache/apt \
    apt-get update && apt-get install -y git

# Install dependencies
COPY requirements.txt .
#RUN pip install -r requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    cat requirements.txt | xargs -n 1 pip install

COPY . .

