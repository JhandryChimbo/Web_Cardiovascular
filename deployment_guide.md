# Guía de Despliegue - CardioGuard AI

Este repositorio ha sido configurado para ser desplegado de forma rápida y sencilla. Tienes dos opciones principales de despliegue:
1. **Despliegue Híbrido (Recomendado):** Backend en **Render** (ideal para servidores de Python/FastAPI) y Frontend en **Vercel** (Cargado en segundos a través de su CDN global).
2. **Despliegue Todo en Render:** Tanto Backend como Frontend corriendo en **Render** mediante el archivo de Blueprint unificado.

---

## 🛠️ Archivos de Configuración Creados

Hemos añadido y modificado los siguientes archivos para preparar la infraestructura:
- [backend/requirements.txt](./backend/requirements.txt): Declaración de librerías de Python (FastAPI, Scikit-Learn, XGBoost, etc.) con versiones exactas compatibles.
- [render.yaml](./render.yaml): Blueprint de Render para auto-configurar los servicios en un solo clic.
- [vercel.json](./vercel.json): Configura el enrutamiento para que Vercel sirva directamente los archivos estáticos de la carpeta `frontend/`.
- [backend/main.py](./backend/main.py): Añadido endpoint de verificación `GET /` para healthchecks en producción.
- [frontend/index.html](./frontend/index.html): Añadido panel dinámico de configuración del Servidor API (con icono de ⚙️ en el sidebar) para cambiar la URL de producción sin modificar código en el futuro.

---

## 🚀 Opción 1: Despliegue Híbrido (Render + Vercel)

### Paso A: Desplegar el Backend en Render
1. Inicia sesión en [Render](https://render.com/).
2. Haz clic en **New +** y selecciona **Web Service**.
3. Conecta tu repositorio de GitHub.
4. Rellena la configuración básica del Web Service:
   - **Name:** `cardio-backend` (o el que desees)
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** `Free`
5. Haz clic en **Create Web Service**.
6. Una vez completado el despliegue, copia la **URL del servicio** generada (en tu caso: `https://web-cardiovascular.onrender.com`).

> [!NOTE]
> La primera petición a un servicio gratuito de Render puede tardar unos 50 segundos en responder debido a que el servidor entra en estado de suspensión (cold start) si no recibe tráfico en 15 minutos.

---

### Paso B: Desplegar el Frontend en Vercel
1. Inicia sesión en [Vercel](https://vercel.com/).
2. Haz clic en **Add New** > **Project**.
3. Selecciona tu repositorio de GitHub e impórtalo.
4. **Vercel detectará automáticamente tu `vercel.json`** y configurará la ruta de la carpeta `frontend/` sin que tengas que hacer nada.
5. Deja los comandos de construcción y directorios de salida por defecto (vacíos).
6. Haz clic en **Deploy**.
7. ¡Listo! Vercel te dará una URL para tu frontend (ej. `https://cardio-guard-ai.vercel.app`).

---

### Paso C: Conectar el Frontend con el Backend
1. Abre tu sitio web desplegado en Vercel.
2. En la barra lateral izquierda, verás el indicador **Servidor API: Modo Simulador** (o buscando conexión).
3. Haz clic en el **icono de engranaje (⚙️)** al lado del indicador.
4. Pega la URL de tu backend de Render (en tu caso: `https://web-cardiovascular.onrender.com`) en el campo de texto.
5. Haz clic en **Guardar**.
6. El indicador cambiará a **Servidor API: Conectado** en verde, y a partir de ese momento las inferencias se realizarán directamente contra tu modelo XGBoost en Render. Esta configuración se guarda en el navegador (`localStorage`) por lo que no tendrás que ingresarla cada vez.

---

## 🚀 Opción 2: Despliegue Todo en Render (Blueprint)

Si prefieres tener todo unificado en un solo panel de Render:
1. Inicia sesión en [Render](https://render.com/).
2. Ve a **Blueprints** en la barra superior.
3. Haz clic en **New Blueprint Instance**.
4. Conecta tu repositorio.
5. Render leerá el archivo `render.yaml` automáticamente y configurará dos servicios:
   - `web-cardio-backend` (Servidor API de Python)
   - `web-cardio-frontend` (Página web estática)
6. Haz clic en **Approve** para iniciar el despliegue automático de ambos.
7. Una vez listos, ve a la URL del frontend en Render, haz clic en el engranaje de configuración y apunta la URL al backend de Render.
