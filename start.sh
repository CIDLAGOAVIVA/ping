#!/bin/bash
# Quick start script - apenas inicia a aplicação

cd `dirname $0`
nohup uv run python app.py "$@" >/var/log/cid-ping.log 2>&1 &
