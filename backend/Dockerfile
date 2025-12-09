# backend/Dockerfile (production)
FROM python:3.11-slim

# set workdir
WORKDIR /app

# system deps for some Python packages
RUN apt-get update && apt-get install -y gcc libpq-dev build-essential --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

# copy only dependency files first for caching
COPY backend/requirements.txt /app/requirements.txt

# install python deps
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r /app/requirements.txt

# copy application code
COPY backend/ /app/

# create non-root user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# DEFAULT CMD — adjust left-hand side (module:path) if your entrypoint differs
# Common entrypoints: main:app, app.main:app, src.main:app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

# Alternative CMD using Gunicorn with Uvicorn workers for production
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "main:app", "-w", "4", "-b", "0.0.0.0:8000"]



#FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8
## Set environment varibles
#ENV PYTHONDONTWRITEBYTECODE 1
#ENV PYTHONUNBUFFERED 1
#
## Set the working directory inside the container
#WORKDIR /app
#
## Install the Python dependencies
#RUN pip install pipenv --upgrade
##RUN /usr/bin/pip3 install pipenv
#
##COPY ./app/Pipfile ./app/Pipfile.lock /containerworkdir/ #when using docker build
##COPY Pipfile Pipfile.lock ./
#COPY Pipfile Pipfile.lock ./
#RUN pipenv install --system --dev --deploy --ignore-pipfile
##RUN pipenv install --deploy
#
## Copy the application code to the working directory
##COPY . /code
#COPY ./app .
## Expose the port on which the application will run
#EXPOSE 80
#
## Run the specified command within the container.
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload", "--forwarded-allow-ips='*'"]
##CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
#
