@echo off
echo Starting Fake Food Detection Server...

REM Set environment variables to suppress TensorFlow warnings
set TF_ENABLE_ONEDNN_OPTS=0
set TF_CPP_MIN_LOG_LEVEL=2

REM Navigate to webapp directory
cd webapp

REM Run Django development server
python manage.py runserver

pause