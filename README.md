# APP DNI - Fecha de Nacimiento

App web que busca la fecha de nacimiento a partir del nombre y apellidos de una persona, consultando la API de [apis.net.pe](https://apis.net.pe).

---

## Requisitos

- Python 3.10 o superior instalado
- Token gratuito de [apis.net.pe](https://apis.net.pe/app)

---

## Instalación (solo la primera vez)

Abre la terminal en la carpeta del proyecto y ejecuta:

```
pip install -r requirements.txt
```

---

## Configurar el Token

1. Regístrate gratis en https://apis.net.pe/app
2. Copia tu token
3. Abre el archivo `.env` y reemplaza `AQUI_VA_TU_TOKEN` con tu token real:

```
API_TOKEN=eyJhbGciOi...tu_token_aqui
```

---

## Ejecutar la app

```
uvicorn main:app --reload
```

Luego abre el navegador en: **http://localhost:8000**

---

## ¿Cómo funciona?

1. Ingresas nombres y apellidos en el formulario
2. La app busca el DNI usando la API externa
3. Con ese DNI obtiene la fecha de nacimiento
4. Muestra solo la fecha en pantalla
