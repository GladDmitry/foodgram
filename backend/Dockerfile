FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

RUN useradd -u 1000 -g 1001 yc-user

COPY . .

RUN chown -R yc-user:yc-user /app

USER yc-user

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi"]