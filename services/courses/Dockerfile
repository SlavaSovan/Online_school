FROM python:3.13.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x prestart.sh

EXPOSE 8000

ENTRYPOINT [ "./prestart.sh" ]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]