FROM python:3.9-slim

WORKDIR /app

# Copiar los archivos necesarios
COPY requirements.txt .
COPY fastAPI.py .
COPY example.env .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Variable de entorno para Python
ENV PYTHONUNBUFFERED=1

# Puerto en el que se ejecutará la aplicación
EXPOSE 8000

# Comando para iniciar la aplicación
CMD ["uvicorn", "fastAPI:app", "--host", "0.0.0.0", "--port", "8000"] 