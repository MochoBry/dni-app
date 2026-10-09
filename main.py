from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import re
from playwright.sync_api import sync_playwright

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


def buscar_datos_sync(nombres: str, apellido_paterno: str, apellido_materno: str):
    """
    Ejecuta el flujo completo de 2 pasos en dniperu.com:
    1. Buscar DNI a partir de nombres y apellidos
    2. Con ese DNI, buscar la fecha de nacimiento
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )

        try:
            # --- PASO 1: Buscar DNI por nombre ---
            page.goto("https://dniperu.com/buscar-dni-por-nombre/", timeout=30000)
            page.fill("input[name=nombres]", nombres)
            page.fill("input[name=apellido_paterno]", apellido_paterno)
            page.fill("input[name=apellido_materno]", apellido_materno)
            page.click("button[type=submit]")
            page.wait_for_timeout(4000)

            text1 = page.evaluate("document.body.innerText")
            lines1 = [l.strip() for l in text1.split("\n") if l.strip()]

            dni = None
            for i, l in enumerate(lines1):
                if l.upper() == "COPIAR" and i > 0:
                    posible_dni = lines1[i - 1]
                    if re.match(r"^\d{8}$", posible_dni):
                        dni = posible_dni
                        break

            if not dni:
                return None, None, "No se encontró ningún DNI para esos nombres y apellidos en la base pública."

            # --- PASO 2: Buscar Fecha de Nacimiento por DNI ---
            page.goto("https://dniperu.com/fecha-de-nacimiento-con-dni/", timeout=30000)
            page.fill("input[name=dni]", dni)
            page.click("button[type=submit]")
            page.wait_for_timeout(4000)

            text2 = page.evaluate("document.body.innerText")
            lines2 = [l.strip() for l in text2.split("\n") if l.strip()]

            fecha = None
            for i, l in enumerate(lines2):
                if l.upper() == "FECHA DE NACIMIENTO" and i + 1 < len(lines2):
                    posible_fecha = lines2[i + 1]
                    if re.match(r"^\d{2}/\d{2}/\d{4}$", posible_fecha):
                        fecha = posible_fecha
                        break

            if not fecha:
                return dni, None, f"Se encontró el DNI ({dni}), pero la fecha de nacimiento no está disponible."

            return dni, fecha, None

        except Exception as e:
            return None, None, f"Error durante la consulta: {str(e)}"
        finally:
            browser.close()


def render_page(
    nombres="",
    apellido_paterno="",
    apellido_materno="",
    resultado_html="",
):
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Consulta Fecha de Nacimiento</title>
  <link rel="stylesheet" href="/static/style.css" />
</head>
<body>
  <div class="card">
    <h1>🪪 Consulta de Fecha de Nacimiento</h1>
    <p class="subtitle">Ingresa el nombre completo para obtener la fecha de nacimiento.</p>

    <form method="post" action="/consultar">
      <div class="form-group">
        <label for="nombres">Nombres</label>
        <input type="text" id="nombres" name="nombres"
               placeholder="Ej: BRYAN BRANDON"
               value="{nombres}" required autocomplete="off" />
      </div>
      <div class="form-row">
        <div class="form-group">
          <label for="apellido_paterno">Apellido Paterno</label>
          <input type="text" id="apellido_paterno" name="apellido_paterno"
                 placeholder="Ej: HUASASQUICHE"
                 value="{apellido_paterno}" required autocomplete="off" />
        </div>
        <div class="form-group">
          <label for="apellido_materno">Apellido Materno</label>
          <input type="text" id="apellido_materno" name="apellido_materno"
                 placeholder="Ej: ZORRILLA"
                 value="{apellido_materno}" required autocomplete="off" />
        </div>
      </div>
      <button type="submit" id="btn-consultar">Consultar</button>
    </form>

    {resultado_html}
  </div>

  <script>
    const form = document.querySelector('form');
    const btn = document.getElementById('btn-consultar');
    form.addEventListener('submit', () => {{
        btn.innerText = 'Consultando datos (⏳ Por favor espera unos segundos)...';
        btn.style.opacity = '0.7';
        btn.disabled = true;
    }});
  </script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(render_page())


@app.post("/consultar", response_class=HTMLResponse)
async def consultar(
    nombres: str = Form(...),
    apellido_paterno: str = Form(...),
    apellido_materno: str = Form(...),
):
    nombres_clean = nombres.strip().upper()
    apellido_paterno_clean = apellido_paterno.strip().upper()
    apellido_materno_clean = apellido_materno.strip().upper()

    # Ejecutamos el scraping sincrónico en un hilo separado para evitar incompatibilidades en Windows
    dni, fecha, error = await asyncio.to_thread(
        buscar_datos_sync,
        nombres_clean,
        apellido_paterno_clean,
        apellido_materno_clean,
    )

    if error:
        resultado_html = f"""
        <div class="result error">
          <span class="icon">⚠️</span>
          <p>{error}</p>
        </div>"""
    elif fecha:
        nombre_completo = f"{nombres_clean} {apellido_paterno_clean} {apellido_materno_clean}"
        resultado_html = f"""
        <div class="result success">
          <span class="icon">🎂</span>
          <div>
            <p class="result-name">{nombre_completo}</p>
            <p class="result-label" style="font-size: 0.9em; margin-bottom: 5px; opacity: 0.85;">DNI: {dni}</p>
            <p class="result-label">Fecha de nacimiento</p>
            <p class="result-date">{fecha}</p>
          </div>
        </div>"""
    else:
        resultado_html = ""

    return HTMLResponse(
        render_page(
            nombres=nombres,
            apellido_paterno=apellido_paterno,
            apellido_materno=apellido_materno,
            resultado_html=resultado_html,
        )
    )
