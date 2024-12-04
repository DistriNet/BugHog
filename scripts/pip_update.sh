#!/bin/sh

pip-compile -U requirements.in
pip-compile -U requirements_dev.in
