# under hivemind celery worker detects its running under console and try to
# do something funny. use tee to workaround this problem
worker: celery worker --app=app.celery --loglevel=info -B | tee /dev/null
flower: celery flower --app=app.celery --port=5555
web: flask run
