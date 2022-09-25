# syntax=docker/dockerfile:1
FROM python:3.10-slim


# By copying over requirements first, we make sure that Docker will cache
# our installed requirements rather than reinstall them on every build
RUN mkdir /code
WORKDIR /code

COPY requirements.txt .

#COPY Pipfile .
#
#RUN pip install --upgrade pip && \
#    pip install pipenv && \
#    apt-get update && \
#    apt-get upgrade -y && \
#    apt-get install -y --no-install-recommends libmariadb-dev python3-dev build-essential && \
#    pipenv lock && \
#    pipenv install --system --deploy && \
#    pip uninstall -y pipenv && \
#    apt-get purge -y python3-dev build-essential && \
#    apt-get autoremove -y && \
#    apt-get clean && \
#    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends libmariadb-dev python3-dev build-essential
RUN pip install -r requirements.txt
RUN apt-get purge -y python3-dev build-essential && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY app.py .
COPY config.json .
COPY mqttlogger .


# Now copy in our code, and run it
CMD ["python", "app.py"]
