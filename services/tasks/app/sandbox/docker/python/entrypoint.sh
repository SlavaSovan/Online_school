#!/bin/bash

# Безопасные настройки Python:
# -I    : Изолированный режим
# -B    : Не создавать .pyc файлы
# -E    : Игнорировать переменные окружения PYTHON*
# -S    : Не импортировать site модуль
# -u    : Небуферизованный вывод
# -OO   : Удаляет docstrings и включает дополнительные оптимизации
# -R    : Randomize hash (security)
exec python3 -I -B -E -S -u -OO -R /sandbox/runner.py