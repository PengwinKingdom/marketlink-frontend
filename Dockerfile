FROM python:3.10-slim

WORKDIR /app

# Copiamos requirements.txt y los instalamos
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código
COPY . .

# Variables de entorno de Flask (opcional pero útil)
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["python", "app.py"]