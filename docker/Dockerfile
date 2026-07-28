FROM python:3.12-alpine

ENV PYTHONUNBUFFERED=1
ENV AUTOBAHN_USE_NVX=0

WORKDIR /
COPY ./requirements.txt .
RUN pip install -r requirements.txt && pip install gunicorn

WORKDIR /app
COPY . .

EXPOSE 80

# Run migrations and server at entrypoint
ENTRYPOINT ["/bin/sh", "./docker/entrypoint.sh"]