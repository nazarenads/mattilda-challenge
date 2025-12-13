# pull official base image
FROM python:3.13-slim-bookworm

# set working directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# install system dependencies
RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# install python dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# add app
COPY . .

# make entrypoint executable
RUN chmod +x entrypoint.sh

# expose port
EXPOSE 8000

# run the application via entrypoint script
CMD ["./entrypoint.sh"]

