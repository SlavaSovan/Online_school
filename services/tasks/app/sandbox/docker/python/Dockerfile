FROM python:3.13.12-slim-trixie

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Рабочая директория
WORKDIR /sandbox 

# Устанавливаем минимальные системные пакеты
RUN apt-get update && \
    apt-get install -y bash && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем ТОЛЬКО то, что нужно для выполнения кода
RUN pip install --no-cache-dir jinja2

# Только чтение и выполнение
RUN chmod 555 /sandbox
RUN chmod a-w /sandbox

# Entrypoint скрипт
COPY entrypoint.sh /entrypoint.sh
RUN chmod 555 /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]