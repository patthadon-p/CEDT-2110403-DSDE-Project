@echo off
echo Formatting code...
ruff check --fix .
black .
isort .
echo Done!