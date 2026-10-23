@echo off
cd /d "%~dp0"
title Dashboard SP

echo Verificando dependencias...
python -m pip install --quiet streamlit pandas geopandas plotly pyarrow openpyxl

echo Iniciando o dashboard...
python -m streamlit run dashboard.py

pause
