import logging
from collections.abc import MutableMapping
from typing import Any
import pytest
import time
import subprocess
from pathlib import Path
import os 
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
app_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../app'))
sys.path.insert(0, app_folder)


directories = [x[0] for x in os.walk(app_folder) if (not '__' in x[0]) and x[0].split('/app')[-1].count('/') == 1]

for path in directories:
    sys.path.insert(0, path)

from dotenv import load_dotenv
load_dotenv('.testenv')
import os
from app.run import app
logging.info(app.title)

docker_compose_file = Path(__file__).parent.joinpath("docker-compose.yaml").resolve()

def docker_comnpose_down():
    cmd = f"docker compose -f {docker_compose_file} down"

    result = subprocess.run(cmd.split(), capture_output=True, text=True)

    if result.returncode != 0:
        logging.error(f"Docker Compose failed to stop: {result.stderr}")
    else:
        logging.info("Docker Compose stoped")


@pytest.fixture(scope="session", autouse=True)
def setup_session():
    try:
        docker_comnpose_down()

        cmd = f"docker compose -f {docker_compose_file} up --build -d"
        result = subprocess.run(cmd.split(), capture_output=True, text=True)

        if result.returncode != 0:
            logging.critical(f"Failed to start Docker Compose: {result.stderr}")
            pytest.exit("Docker Compose failed to start")
        time.sleep(10)
        yield
    finally:
        wait = 10
        logging.info(f"Docker will be stoped in {wait} seconds")
        time.sleep(wait)

        docker_comnpose_down()


def pytest_tavern_beta_before_every_request(request_args: MutableMapping):
    message = f"Request: {request_args['method']} {request_args['url']}"

    params = request_args.get("params", None)
    if params:
        message += f"\nQuery parameters: {params}"

    message += f"\nRequest body: {request_args.get('json', '<no body>')}"

    logging.info(message)


def pytest_tavern_beta_after_every_response(expected: Any, response: Any) -> None:
    logging.info(f"Response: {response.status_code} {response.text}")
