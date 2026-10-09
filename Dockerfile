# Usar imagen oficial de Playwright con Python incluido
FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

WORKDIR /app

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar el navegador Chromium de Playwright
RUN playwright install chromium

# Copiar el código de la aplicación
COPY . .

# Exponer el puerto
EXPOSE 8000

# Comando para iniciar el servidor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
