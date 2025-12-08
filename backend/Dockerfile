FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8
# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Install the Python dependencies
RUN pip install pipenv --upgrade
#RUN /usr/bin/pip3 install pipenv

#COPY ./app/Pipfile ./app/Pipfile.lock /containerworkdir/ #when using docker build
#COPY Pipfile Pipfile.lock ./
COPY Pipfile Pipfile.lock ./
RUN pipenv install --system --dev --deploy --ignore-pipfile
#RUN pipenv install --deploy

# Copy the application code to the working directory
#COPY . /code
COPY ./app .
# Expose the port on which the application will run
EXPOSE 80

# Run the specified command within the container.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload", "--forwarded-allow-ips='*'"]
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]

