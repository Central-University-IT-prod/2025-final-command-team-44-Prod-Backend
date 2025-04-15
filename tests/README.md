### Для запуска тестов выполните команды

python3 -m venv venv
source venv/bin/activate
pip install tavern
pip install --upgrade setuptools
pip install -r requirements.txt

cd /e2e

tavern-ci .
или
pytest --cov-report=html --cov=../../app . (с результатом coverage)
