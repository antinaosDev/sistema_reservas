
<!-- Encabezado con banner -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:FF4B4B,100:1E90FF&height=200&section=header&text=Sistema%20de%20Reserva%20de%20Salas&fontSize=45&fontColor=ffffff&animation=fadeIn&fontAlignY=35"/>
</p>

---


**Versión 2.0 Professional**

Un sistema de gestión inteligente de reserva de salas de reuniones desarrollado con [Streamlit](https://streamlit.io/), que permite a los usuarios solicitar salas, asignar horarios basados en disponibilidad y prioridad, y visualizar el uso de las instalaciones mediante un dashboard interactivo. Los datos se almacenan de forma centralizada en una hoja de cálculo de Google Sheets.

---

## 🔗 Link portafolio

<p align="center">
  <a href="https://share.streamlit.io/user/antinaosdev">
    <img src="https://img.shields.io/badge/Streamlit%20Apps-FF4B4B?logo=streamlit&logoColor=white&style=for-the-badge"/>
  </a>
  <a href="https://github.com/antinaosDev">
    <img src="https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white&style=for-the-badge"/>
  </a>
  <a href="mailto:alain.antinao.s@gmail.com">
    <img src="https://img.shields.io/badge/Email-alain.antinao.s%40gmail.com-red?style=for-the-badge&logo=gmail"/>
  </a>
  <a href="https://alain-antinao-s.notion.site/">
    <img src="https://img.shields.io/badge/Notion-000000?logo=notion&logoColor=white&style=for-the-badge"/>
  </a>
</p>

---

## 🧭 Sobre el Proyecto

**Características Principales:**

*   **Solicitud de Reservas:** Los usuarios pueden solicitar salas de reuniones completando un formulario con detalles como nombre, correo, fecha, rango horario preferido, criterio de prioridad y propósito.
*   **Gestión de Prioridades:** El sistema asigna horarios considerando un sistema de prioridad (1 a 4) para optimizar la utilización del espacio.
*   **Reubicación Inteligente:** Las reservas de menor prioridad solicitadas el mismo día pueden ser reubicadas automáticamente si es necesario para dar cabida a una reserva de mayor prioridad.
*   **Dashboard Interactivo:** Visualización en tiempo real de métricas clave como total de reservas, tasa de ocupación, distribución por día y prioridad, y tendencias mensuales.
*   **Almacenamiento en Google Sheets:** Utiliza Google Sheets como backend para almacenar y gestionar los datos de las reservas de forma colaborativa y persistente.
*   **Gestión de IDs:** Generación automática de IDs únicos para cada reserva basados en la fecha de la reunión (e.g., `RES-20241201-001`).
*   **Gestión de Zonas Horarias:** Manejo centralizado de la hora local (configurable, por defecto Chile Continental) para evitar inconsistencias.
*   **Filtros y Exportación:** En la pestaña de gestión, se pueden filtrar las reservas y descargar la lista en formato CSV.

---

## 📚 Tecnologías Utilizadas

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
  <img src="https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white"/>
  <img src="https://img.shields.io/badge/Pandas-2C2D72?style=for-the-badge&logo=pandas&logoColor=white"/>
  <img src="https://img.shields.io/badge/Google%20Sheets-34A853?style=for-the-badge&logo=google-sheets&logoColor=white"/>
  <img src="https://img.shields.io/badge/Pytz-000000?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white"/>
</p>

---

## 🏗️ Instalación y Uso

### Requisitos

*   Python 3.8 o superior (probado con Python 3.13)
*   Paquetes de Python: `streamlit`, `pandas`, `plotly`, `google-api-python-client`, `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`, `pytz`, `Pillow`
*   Credenciales de Google Cloud Platform (GCP) con acceso a la API de Google Sheets y un archivo de credenciales de servicio (JSON).
*   Una hoja de cálculo de Google Sheets con la estructura correcta y permisos configurados para el servicio de credenciales.

### Instalación

1.  **Clona o descarga** este repositorio en tu entorno local.
2.  **Crea un entorno virtual** (opcional pero recomendado):
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```
3.  **Instala las dependencias:**
    ```bash
    pip install streamlit pandas plotly google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2 pytz Pillow
    ```
4.  **Configura Google Sheets:**
    *   Crea un proyecto en Google Cloud Console.
    *   Habilita la API de Google Sheets para el proyecto.
    *   Crea una credencial de **Cuenta de Servicio**.
    *   Descarga el archivo JSON de credenciales.
    *   Comparte la hoja de cálculo de Google Sheets con el **correo electrónico de la cuenta de servicio** (lo encontrarás en el archivo JSON).
    *   Copia el **ID de la hoja de cálculo** (es la parte larga del ID en la URL de la hoja).
    *   Crea un archivo en tu proyecto llamado `.streamlit/secrets.toml`.
    *   Pega el contenido del archivo JSON de credenciales dentro del archivo `secrets.toml` bajo una clave específica, por ejemplo:
        ```toml
        # .streamlit/secrets.toml
        [secrets]
        google_sheets_creds = '''
        {
          "type": "service_account",
          "project_id": "tu-proyecto-id",
          "private_key_id": "xxxxxxx",
          "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
          "client_email": "tu-cuenta-de-servicio@tu-proyecto.iam.gserviceaccount.com",
          "client_id": "123456789012345678901",
          "auth_uri": "https://accounts.google.com/o/oauth2/auth",
          "token_uri": "https://oauth2.googleapis.com/token",
          "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
          "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/tu-cuenta-de-servicio%40tu-proyecto.iam.gserviceaccount.com",
          "universe_domain": "googleapis.com"
        }
        '''
        ```
    *   **Importante:** Asegúrate de que la estructura de la hoja de cálculo en Google Sheets coincida con las columnas esperadas por el código: `['id', 'nombre', 'email', 'fecha', 'hora_inicio_rango', 'hora_fin_rango', 'hora_inicio', 'hora_fin', 'criterio', 'num_asistentes', 'proposito', 'fecha_reserva']`. La primera fila debe contener estos encabezados exactamente.

5.  **Actualiza el ID de la hoja de cálculo:**
    *   Abre el archivo `main.py` (o como lo hayas nombrado).
    *   Busca la línea `SPREADSHEET_ID = '...'` y reemplaza el valor con el ID de tu hoja de cálculo de Google Sheets.

6.  **Actualiza las rutas de los logos (opcional):**
    *   Si usas imágenes para el logo en el dashboard o el footer, asegúrate de que los archivos `CESFAM.jpg` y `logo_alain.png` estén en la misma carpeta que tu script de Python, o actualiza las rutas en las líneas donde se cargan (`load_logo("...")`).

### Uso

1.  Abre tu terminal o consola de comandos.
2.  Navega hasta la carpeta donde tienes el archivo `main.py`.
3.  Activa tu entorno virtual si lo usaste (p. ej., `source venv/bin/activate`).
4.  Ejecuta el comando:
    ```bash
    streamlit run main.py
    ```
5.  Tu navegador predeterminado debería abrirse con la aplicación Streamlit.

---

## ✨ Logros Destacados

- 🧠 **Gestión Inteligente:** Sistema automatizado que gestiona prioridades y reubicaciones para optimizar el uso de salas.
- 💾 **Almacenamiento Robusto:** Integración con Google Sheets para persistencia de datos y colaboración.
- 📊 **Visualización Clara:** Dashboard interactivo para monitorear el uso de las salas.
- ⏰ **Gestión de Horarios:** Validación y manejo centralizado de zonas horarias y horarios de operación.

---

## 📬 Contacto

📧 **Email:** [alain.antinao.s@gmail.com](mailto:alain.antinao.s@gmail.com)  
💼 **GitHub:** [antinaosDev](https://github.com/antinaosDev)  
🌍 Ubicado en Chile — Disponible para colaboraciones internacionales  

---

<!-- Footer con banner -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:1E90FF,100:FF4B4B&height=120&section=footer"/>
</p>



