#!/bin/bash
cd "$(dirname "$0")"/rechenknecht
uwsgi --http-socket localhost:8080 --plugin=python3 --manage-script-name --mount /=main:app
