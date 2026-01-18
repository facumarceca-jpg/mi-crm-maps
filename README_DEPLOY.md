# Cómo ejecutar y publicar tu Web App (CRM)

Tu código actual (`app.py`) **YA ES una aplicación web** completa construida con **Streamlit**. No necesitas reescribirlo.

## 1. Ver desde el Celular (Misma WiFi) - ¡Más Rápido!
Si solo quieres probarlo en tu celular y estás conectado al mismo WiFi que tu PC:

1.  Abre la terminal en tu PC y ejecuta:
    ```powershell
    streamlit run app.py
    ```
2.  En la terminal verás algo como:
    ```
    Network URL: http://192.168.1.XX:8501
    ```
3.  Escribe esa dirección **exacta** en el navegador de tu celular.
    *Nota: Debes asegurarte que tu Firewall de Windows permita la conexión a Python.*

## 2. Publicar en Internet (Streamlit Cloud)
Para tener un link accesible desde cualquier lado (fuera de casa):

**⚠️ IMPORTANTE SOBRE DATOS CREADOS:**
Como tu app guarda datos en un archivo local (`leads_db.csv`), en Streamlit Cloud **los cambios se perderán** si la app se reinicia (algo común en la nube). Para un uso serio en la nube, necesitarías conectar una base de datos externa (Google Sheets, Firestore, etc.).

**Pasos:**
1.  **Sube tu código a GitHub** (archivos `app.py`, `requirements.txt`, `google.csv`).
2.  Ve a [share.streamlit.io](https://share.streamlit.io/) e inicia sesión con GitHub.
3.  Dale a "New app", selecciona tu repositorio y el archivo `app.py`.
4.  Dale a **Deploy**.

Tu archivo `requirements.txt` ya tiene lo necesario.
