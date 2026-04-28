import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json  # Añadido para manejar el archivo JSON de credenciales
from PIL import Image
import pytz  # <-- Importación añadida para manejo de zonas horarias
from streamlit_calendar import calendar
import json  # Añadido para manejar el archivo JSON de credenciales

# from streamlit_calendar import calendar # <-- Importación comentada para evitar el error
# --- Definición de Zona Horaria ---
# Define la zona horaria de Chile Continental (CLT) o la que corresponda
# Asegúrate de usar el nombre correcto de la zona horaria, por ejemplo:
# 'America/Santiago' para Chile Continental
# 'Pacific/Auckland' para Nueva Zelanda
# 'Europe/London' para Reino Unido
ZONA_HORARIA_LOCAL = pytz.timezone(
    "America/Santiago"
)  # <-- Cambia esto si es necesario


# --- Fin Definición de Zona Horaria ---
# --- Funciones de Utilidad ---
def obtener_hora_local():
    """Obtiene la hora actual en la zona horaria local definida."""
    utc_now = datetime.now(pytz.utc)  # Obtiene la hora UTC actual
    hora_local = utc_now.astimezone(
        ZONA_HORARIA_LOCAL
    )  # Convierte a la zona horaria local
    return hora_local


def es_dia_habil(fecha):
    """Verifica si una fecha es día hábil (lunes a viernes)."""
    return fecha.weekday() < 5


def calcular_dias_habiles(fecha_inicio, fecha_fin):
    """Calcula la cantidad de días hábiles entre dos fechas (excluyendo inicio, incluyendo fin)."""
    if fecha_inicio >= fecha_fin:
        return 0

    dias_habiles = 0
    fecha_actual = fecha_inicio + timedelta(
        days=1
    )  # Comenzamos desde el día siguiente al inicio
    while fecha_actual <= fecha_fin:
        if es_dia_habil(fecha_actual):
            dias_habiles += 1
        fecha_actual += timedelta(days=1)
    return dias_habiles


# --- Fin Funciones de Utilidad ---
@st.cache_resource
def load_logo(path):
    return Image.open(path)


# --- Integración con Google Sheets usando secrets ---
from googleapiclient.discovery import build
from google.oauth2 import service_account
import streamlit as st  # Asegúrate de importar st aquí si no está
import json  # Asegúrate de importar json aquí si no está

# Alcances requeridos para trabajar con Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
try:
    # Intenta obtener las credenciales del archivo secrets.toml
    # Accede al secret definido como google_sheets_creds
    creds_info = json.loads(st.secrets["google_sheets_creds"])
    creds = service_account.Credentials.from_service_account_info(
        creds_info, scopes=SCOPES
    )
    # st.success("✅ Credenciales de Google Sheets cargadas desde secrets.")
except KeyError:
    st.error(
        "❌ Error: No se encontró el secret 'google_sheets_creds' en secrets.toml."
    )
    st.stop()  # Detiene la ejecución si no hay credenciales
except Exception as e:
    st.error(f"❌ Error al cargar las credenciales desde secrets: {e}")
    st.stop()  # Detiene la ejecución si hay un error al cargarlas
# Construir el servicio de Google Sheets API (esta parte no cambia)
service = build("sheets", "v4", credentials=creds)
# ID de la hoja de cálculo (reemplaza con tu propio ID)
SPREADSHEET_ID = "1ojDb593qqFO0xDmbYNzpNWI4gwbbQpVXEt8ggPHIwYg"
SHEET_NAME = "Hoja 1"  # Nombre de la hoja donde se almacenan las reservas
# --- Retry Logic for Google Sheets API ---
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from googleapiclient.errors import HttpError


def es_error_reintentable(exception):
    """Verifica si el error es un 5xx reintentable de la API de Google."""
    if isinstance(exception, HttpError):
        return exception.resp.status in [500, 502, 503, 504]
    return False


decorador_retry = retry(
    retry=retry_if_exception(es_error_reintentable),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(5),
    reraise=True,
)


@decorador_retry
def _ejecutar_api_cargar(range_name):
    """Carga datos con reintentos."""
    return (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=SPREADSHEET_ID, range=range_name)
        .execute()
    )


@decorador_retry
def _ejecutar_api_append(range_name_append, body):
    """Inserta datos con reintentos."""
    return (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name_append,
            valueInputOption="USER_ENTERED",
            body=body,
        )
        .execute()
    )


# --- Fin Retry Logic ---
# --- Fin Integración Google Sheets ---
# Configuración de la página
st.set_page_config(
    page_title="Sistema de Reserva | Gestión Inteligente",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)
# CSS personalizado para diseño profesional
st.markdown(
    """
<style>
    /* Fuentes y colores principales */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    /* Header personalizado */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }
    /* Tarjetas de métricas */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border-left: 4px solid #667eea;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #667eea;
        margin: 0;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.5rem;
    }
    .metric-delta {
        font-size: 0.85rem;
        color: #10b981;
        margin-top: 0.5rem;
    }
    /* Sidebar mejorado */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    /* Botones personalizados */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(102,126,234,0.3);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102,126,234,0.4);
    }
    /* Alertas personalizadas */
    .success-box {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(16,185,129,0.2);
    }
    .info-box {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(59,130,246,0.2);
    }
    .warning-box {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(245,158,11,0.2);
    }
    /* Tabla mejorada */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }
    /* Sección de formulario */
    .form-section {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 2rem;
    }
    /* Badge de prioridad */
    .priority-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .priority-1 { background: #ef4444; color: white; }
    .priority-2 { background: #f59e0b; color: white; }
    .priority-3 { background: #3b82f6; color: white; }
    .priority-4 { background: #6b7280; color: white; }
    /* Divider personalizado */
    .custom-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
        margin: 2rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)
# Mapeo de criterios a valores numéricos de prioridad
CRITERIO_PRIORIDAD = {
    "1 - Supervisión de Referentes": 1,
    "2 - Reuniones con la Comunidad": 2,
    "3 - Reuniones de Equipos": 3,
    "4 - Reuniones Generales (mínimo 4 personas)": 4,
}


def obtener_color_prioridad(criterio):
    """Retorna el color según el criterio de prioridad."""
    colores = {
        "1 - Supervisión de Referentes": "#FF6B6B",
        "2 - Reuniones con la Comunidad": "#FFA94D",
        "3 - Reuniones de Equipos": "#FFE066",
        "4 - Reuniones Generales (mínimo 4 personas)": "#69DB7C",
    }
    return colores.get(criterio, "#74C0FC")


HORA_INICIO_DIA = time(8, 0)
HORA_FIN_DIA = time(17, 0)


# --- Funciones de Interacción con Google Sheets ---
def cargar_reservas_desde_sheets():
    """Carga las reservas desde la hoja de cálculo de Google."""
    try:
        range_name = (
            f"'{SHEET_NAME}'!A:L"  # Asumiendo columnas A a L (con fecha_reserva)
        )
        result = _ejecutar_api_cargar(range_name)
        values = result.get("values", [])
        if not values:
            print("No se encontraron datos en la hoja de cálculo.")
            return []
        # Convertir las filas en diccionarios
        headers = values[0]  # La primera fila son los encabezados
        rows = values[1:]  # Las siguientes son los datos
        # Asegurarse de que los encabezados sean los esperados (tu estructura actualizada)
        expected_headers = [
            "id",
            "nombre",
            "email",
            "fecha",
            "hora_inicio_rango",
            "hora_fin_rango",
            "hora_inicio",
            "hora_fin",
            "criterio",
            "num_asistentes",
            "proposito",
            "fecha_reserva",
        ]  # Con 'fecha_reserva'
        if len(headers) != len(expected_headers) or headers != expected_headers:
            st.error(
                f"⚠️ La estructura de la hoja '{SHEET_NAME}' no coincide con la esperada. "
                f"Encabezados actuales: {headers}, Encabezados esperados: {expected_headers}"
            )
            print(
                f"Error: Encabezados no coinciden. Actuales: {headers}, Esperados: {expected_headers}"
            )
            return []  # Devolver lista vacía si no coinciden
        reservas = []
        for i, row in enumerate(
            rows, start=2
        ):  # Empezar en 2 porque la fila 1 son encabezados
            if len(row) >= len(
                headers
            ):  # Asegurarse de que la fila tiene suficientes columnas
                reserva_dict = {
                    headers[j]: row[j] if j < len(row) else ""
                    for j in range(len(headers))
                }
                # Convertir campos numéricos y de fecha/hora si es necesario
                # Por ejemplo, num_asistentes debe ser int
                try:
                    reserva_dict["num_asistentes"] = int(
                        reserva_dict.get("num_asistentes", 0)
                    )
                except ValueError:
                    reserva_dict["num_asistentes"] = (
                        0  # Valor por defecto si no es un número
                    )
                    print(
                        f"Advertencia: 'num_asistentes' no es un número en la fila {i}, usando 0. Valor: {row}"
                    )

                # El ID es string, no lo convertimos a int
                # Validar que la fecha tenga un formato correcto
                fecha_str = reserva_dict.get("fecha", "")
                if fecha_str:
                    try:
                        datetime.strptime(fecha_str, "%Y-%m-%d")
                    except ValueError:
                        print(
                            f"Advertencia: Formato de fecha inválido en la fila {i}: {fecha_str}, saltando fila."
                        )
                        continue  # Saltar esta fila si la fecha es inválida
                # Añadir duracion_horas como campo temporal con valor por defecto para la lógica
                reserva_dict["duracion_horas"] = (
                    1.5  # Valor por defecto para reservas existentes
                )
                # Manejar fecha_reserva
                if not reserva_dict.get("fecha_reserva"):
                    # Asignar un valor por defecto si la celda está vacía
                    reserva_dict["fecha_reserva"] = "1900-01-01 00:00:00"
                reservas.append(reserva_dict)
            else:
                print(
                    f"Fila {i} con datos insuficientes (menos de {len(headers)} columnas): {row}, saltando fila."
                )
        return reservas
    except Exception as e:
        print(f"Error al cargar reservas desde Google Sheets: {e}")
        st.error(f"Error al cargar datos: {e}")
        return []


def guardar_reserva_en_sheets(reserva):
    """Guarda una nueva reserva en la hoja de cálculo de Google."""
    try:
        # Asumiendo que el ID ya está calculado o asignado antes de llamar esta función
        # Si no tiene ID, calcularlo (esto no debería ocurrir en el flujo principal ahora)
        if "id" not in reserva or not reserva["id"]:
            print(
                "Advertencia: Se intentó guardar una reserva sin ID. Esto no debería ocurrir normalmente."
            )
            # Opcional: Generar ID aquí como respaldo, pero el flujo principal debería haberlo hecho
            todas_las_reservas = cargar_reservas_desde_sheets()
            fecha_reserva = reserva.get("fecha", datetime.now().strftime("%Y-%m-%d"))
            id_fecha = fecha_reserva.replace("-", "")
            prefijo = f"RES-{id_fecha}-"
            reservas_fecha = [
                r for r in todas_las_reservas if r.get("id", "").startswith(prefijo)
            ]
            max_numero = 0
            for r in reservas_fecha:
                id_r = r.get("id", "")
                if id_r.startswith(prefijo):
                    try:
                        numero = int(id_r[len(prefijo) :])
                        if numero > max_numero:
                            max_numero = numero
                    except ValueError:
                        continue
            nuevo_numero = max_numero + 1
            reserva["id"] = f"{prefijo}{nuevo_numero:03d}"
        # Preparar la fila para insertar
        # El orden debe coincidir con el de las columnas en la hoja (A a L) - SIN duracion_horas
        fila_a_insertar = [
            reserva.get("id", ""),
            reserva.get("nombre", ""),
            reserva.get("email", ""),
            reserva.get("fecha", ""),
            reserva.get("hora_inicio_rango", ""),
            reserva.get("hora_fin_rango", ""),
            reserva.get("hora_inicio", ""),
            reserva.get("hora_fin", ""),
            reserva.get("criterio", ""),
            str(reserva.get("num_asistentes", 0)),
            reserva.get("proposito", ""),
            reserva.get("fecha_reserva", ""),
            # 'prioridad_num' no se guarda explícitamente en la hoja, se calcula al cargar
            # 'duracion_horas' tampoco se guarda
        ]
        # Insertar la fila al final de la hoja
        range_name_write = (
            f"'{SHEET_NAME}'!A{1000000}"  # Insertar en una fila muy baja o usar append
        )
        # Opcional: Usar append para añadir al final
        _ejecutar_api_append(f"'{SHEET_NAME}'", {"values": [fila_a_insertar]})
        print(f"Reserva guardada exitosamente en Google Sheets con ID {reserva['id']}.")
        return reserva["id"]
    except Exception as e:
        print(f"Error al guardar reserva en Google Sheets: {e}")
        st.error(f"Error al guardar la reserva: {e}")
        return ""  # Indicar fallo


# --- Fin Funciones Google Sheets ---
# Funciones auxiliares (mantienen la misma lógica original, pero adaptadas para usar Google Sheets)
def cargar_reservas():
    # Ahora carga desde Google Sheets
    if "reservas_db" not in st.session_state:
        st.session_state.reservas_db = cargar_reservas_desde_sheets()
    return st.session_state.reservas_db


def guardar_reserva(reserva):
    # Ahora guarda en Google Sheets
    # No necesitamos mantener una lista local en session_state para escritura,
    # solo leer desde la hoja.
    # Calculamos el ID aquí si no lo tiene (esto no debería ocurrir en el flujo principal ahora)
    if "id" not in reserva or not reserva["id"]:
        print(
            "Advertencia: Se intentó guardar una reserva sin ID. Esto no debería ocurrir normalmente."
        )
        todas_las_reservas = cargar_reservas_desde_sheets()
        fecha_reserva = reserva.get("fecha", datetime.now().strftime("%Y-%m-%d"))
        id_fecha = fecha_reserva.replace("-", "")
        prefijo = f"RES-{id_fecha}-"
        reservas_fecha = [
            r for r in todas_las_reservas if r.get("id", "").startswith(prefijo)
        ]
        max_numero = 0
        for r in reservas_fecha:
            id_r = r.get("id", "")
            if id_r.startswith(prefijo):
                try:
                    numero = int(id_r[len(prefijo) :])
                    if numero > max_numero:
                        max_numero = numero
                except ValueError:
                    continue
        nuevo_numero = max_numero + 1
        reserva["id"] = f"{prefijo}{nuevo_numero:03d}"
    id_guardado = guardar_reserva_en_sheets(reserva)
    # Opcional: Forzar recarga de la lista principal después de guardar
    # Esto asegura que la lista local en session_state esté actualizada
    # si se accede a ella inmediatamente después de guardar.
    st.session_state.reservas_db = cargar_reservas_desde_sheets()
    return id_guardado


# NUEVA FUNCIÓN: Genera un ID único basado en la fecha de la reunión
def generar_id_unica_para_fecha(fecha_reserva_str):
    """Genera un ID único basado en la fecha de la reunión."""
    todas_las_reservas = cargar_reservas_desde_sheets()  # Cargar para calcular el ID
    id_fecha = fecha_reserva_str.replace("-", "")
    prefijo = f"RES-{id_fecha}-"
    # Filtrar reservas con el mismo prefijo de fecha
    reservas_fecha = [
        r for r in todas_las_reservas if r.get("id", "").startswith(prefijo)
    ]
    # Encontrar el número más alto
    max_numero = 0
    for r in reservas_fecha:
        id_r = r.get("id", "")
        if id_r.startswith(prefijo):
            try:
                numero = int(id_r[len(prefijo) :])
                if numero > max_numero:
                    max_numero = numero
            except ValueError:
                continue  # Si no es un número, lo ignora
    nuevo_numero = max_numero + 1
    return f"{prefijo}{nuevo_numero:03d}"  # Formato 001, 002, etc.


def obtener_prioridad(criterio):
    return CRITERIO_PRIORIDAD.get(criterio, 999)


# --- Funciones Modificadas ---


def time_to_minutes(t):
    if isinstance(t, str):
        t = datetime.strptime(t, "%H:%M").time()
    return t.hour * 60 + t.minute


def minutes_to_time(minutes):
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


# --- FUNCIÓN CRÍTICA ACTUALIZADA ---
def verificar_solapamiento(inicio1, fin1, inicio2, fin2):
    """
    Verifica si dos intervalos de tiempo [inicio, fin] se solapan.
    Esta versión considera intervalos cerrados para una detección más estricta,
    evitando que una reunión empiece exactamente cuando termina otra.
    Dos intervalos [i1, f1] y [i2, f2] se solapan si i1 <= f2 AND i2 <= f1.
    """
    i1 = time_to_minutes(inicio1)
    f1 = time_to_minutes(fin1)
    i2 = time_to_minutes(inicio2)
    f2 = time_to_minutes(fin2)

    # Condición de solapamiento para intervalos cerrados
    return i1 <= f2 and i2 <= f1


# --- FIN FUNCIÓN CRÍTICA ACTUALIZADA ---


def validar_plazo_reserva(fecha_reunion, criterio, fecha_solicitud=None):
    """Valida el plazo de reserva basado en días hábiles."""
    if fecha_solicitud is None:
        # Usar la hora local para la validación de plazos
        fecha_solicitud = obtener_hora_local()

    # La fecha de reunión debe ser futura
    if fecha_reunion <= fecha_solicitud.date():
        return False, "La fecha de reunión debe ser futura"

    # Calcular días hábiles entre la fecha de solicitud (día actual) y la fecha de reunión
    dias_habiles = calcular_dias_habiles(fecha_solicitud.date(), fecha_reunion)

    if criterio.startswith("1") or criterio.startswith("2"):
        # Alta prioridad: mínimo 1 día hábil de anticipación
        if dias_habiles < 1:
            return (
                False,
                f"Reservas de alta prioridad requieren mínimo 1 día hábil de anticipación",
            )
    else:
        # Prioridad normal: mínimo 2 días hábiles de anticipación
        if dias_habiles < 2:
            return (
                False,
                f"Reservas ordinarias requieren mínimo 2 días hábiles de anticipación",
            )

    return True, ""


def encontrar_horarios_disponibles_en_rango(
    fecha,
    hora_inicio_rango,
    hora_fin_rango,
    reservas_existentes,
    duracion_requerida_horas,
):
    """Encuentra horarios disponibles considerando la duración requerida (1, 2 o 3 horas)."""
    horarios_disponibles = []
    inicio_rango_min = time_to_minutes(hora_inicio_rango)
    fin_rango_min = time_to_minutes(hora_fin_rango)
    duracion_requerida_minutos = int(duracion_requerida_horas * 60)
    duracion_bloque_minutos = 30  # Bloques de 30 minutos

    tiempo_actual = inicio_rango_min
    while tiempo_actual + duracion_requerida_minutos <= fin_rango_min:
        inicio_propuesto = minutes_to_time(tiempo_actual)
        fin_propuesto = minutes_to_time(tiempo_actual + duracion_requerida_minutos)
        disponible = True
        for reserva in reservas_existentes:
            if reserva["fecha"] == fecha and verificar_solapamiento(
                inicio_propuesto,
                fin_propuesto,
                reserva["hora_inicio"],
                reserva["hora_fin"],
            ):
                disponible = False
                break
        if disponible:
            horarios_disponibles.append((inicio_propuesto, fin_propuesto))
        tiempo_actual += duracion_bloque_minutos  # Avanzar en bloques de 30 minutos
    return horarios_disponibles


def reubicar_reserva(
    reserva_a_reubicar, reservas_fijas, fecha, duracion_requerida_horas
):
    """Reubica una reserva existente a un nuevo horario."""
    fecha_solicitud_reserva = datetime.strptime(
        reserva_a_reubicar["fecha_reserva"], "%Y-%m-%d %H:%M:%S"
    )
    # Usar la hora local para la comparación de fechas
    fecha_actual = obtener_hora_local()
    if fecha_solicitud_reserva.date() != fecha_actual.date():
        return False, None

    # Usar la duración pasada como parámetro, o la de la reserva si no se pasa
    duracion_horas_reserva = duracion_requerida_horas
    horarios_disponibles = encontrar_horarios_disponibles_en_rango(
        fecha, HORA_INICIO_DIA, HORA_FIN_DIA, reservas_fijas, duracion_horas_reserva
    )
    if horarios_disponibles:
        nuevo_inicio, nuevo_fin = horarios_disponibles[0]
        reserva_a_reubicar["hora_inicio"] = nuevo_inicio
        reserva_a_reubicar["hora_fin"] = nuevo_fin
        # --- CÁLCULO AUTOMÁTICO DE DURACIÓN ---
        duracion_calc = (
            time_to_minutes(nuevo_fin) - time_to_minutes(nuevo_inicio)
        ) / 60.0
        reserva_a_reubicar["duracion_horas"] = round(
            duracion_calc, 2
        )  # Asignar duración calculada
        # --- FIN CÁLCULO AUTOMÁTICO DE DURACIÓN ---
        return True, reserva_a_reubicar
    return False, None


def procesar_reserva_con_rango_y_prioridad(nueva_reserva, reservas_existentes):
    """Procesa una nueva reserva, maneja prioridad y conflictos."""
    fecha = nueva_reserva["fecha"]
    prioridad_nueva = obtener_prioridad(nueva_reserva["criterio"])
    hora_inicio_rango = nueva_reserva["hora_inicio_rango"]
    hora_fin_rango = nueva_reserva["hora_fin_rango"]
    # --- NUEVA LÓGICA: Determinar duración requerida ---
    # Asumimos que la duración requerida se basa en el rango preferido o un valor por defecto.
    # Por ejemplo, si el rango es de 2 horas, se busca un bloque de 2 horas.
    duracion_rango_minutos = time_to_minutes(hora_fin_rango) - time_to_minutes(
        hora_inicio_rango
    )
    duracion_rango_horas = duracion_rango_minutos / 60.0
    # Limitar la duración requerida a 1, 2 o 3 horas
    if duracion_rango_horas >= 3:
        duracion_requerida_horas = 3
    elif duracion_rango_horas >= 2:
        duracion_requerida_horas = 2
    elif duracion_rango_horas >= 1:
        duracion_requerida_horas = 1
    else:
        # Si el rango es menor a 1 hora, usar 1 hora como mínimo
        duracion_requerida_horas = 1
    # --- FIN NUEVA LÓGICA ---
    reservas_temporales = [r.copy() for r in reservas_existentes]
    horarios_disponibles = encontrar_horarios_disponibles_en_rango(
        fecha,
        hora_inicio_rango,
        hora_fin_rango,
        reservas_temporales,
        duracion_requerida_horas,
    )

    if horarios_disponibles:
        inicio_asignado, fin_asignado = horarios_disponibles[0]
        nueva_reserva["hora_inicio"] = inicio_asignado
        nueva_reserva["hora_fin"] = fin_asignado
        # --- CÁLCULO AUTOMÁTICO DE DURACIÓN ---
        duracion_calc = (
            time_to_minutes(fin_asignado) - time_to_minutes(inicio_asignado)
        ) / 60.0
        nueva_reserva["duracion_horas"] = round(
            duracion_calc, 2
        )  # Asignar duración calculada
        # --- FIN CÁLCULO AUTOMÁTICO DE DURACIÓN ---
        reservas_temporales.append(nueva_reserva)
        return True, reservas_temporales, (inicio_asignado, fin_asignado), []

    conflictos_en_rango = []
    for reserva_existente in reservas_temporales:
        if reserva_existente["fecha"] == fecha and verificar_solapamiento(
            hora_inicio_rango,
            hora_fin_rango,
            reserva_existente["hora_inicio"],
            reserva_existente["hora_fin"],
        ):
            conflictos_en_rango.append(reserva_existente)

    if not conflictos_en_rango:
        todos_horarios_dia = encontrar_horarios_disponibles_en_rango(
            fecha,
            HORA_INICIO_DIA,
            HORA_FIN_DIA,
            reservas_temporales,
            duracion_requerida_horas,
        )
        horarios_en_rango = []
        for inicio, fin in todos_horarios_dia:
            if verificar_solapamiento(inicio, fin, hora_inicio_rango, hora_fin_rango):
                horarios_en_rango.append((inicio, fin))
        if horarios_en_rango:
            inicio_asignado, fin_asignado = horarios_en_rango[0]
            nueva_reserva["hora_inicio"] = inicio_asignado
            nueva_reserva["hora_fin"] = fin_asignado
            # --- CÁLCULO AUTOMÁTICO DE DURACIÓN ---
            duracion_calc = (
                time_to_minutes(fin_asignado) - time_to_minutes(inicio_asignado)
            ) / 60.0
            nueva_reserva["duracion_horas"] = round(
                duracion_calc, 2
            )  # Asignar duración calculada
            # --- FIN CÁLCULO AUTOMÁTICO DE DURACIÓN ---
            reservas_temporales.append(nueva_reserva)
            return True, reservas_temporales, (inicio_asignado, fin_asignado), []
        else:
            return False, reservas_existentes, None, []

    conflictos_ordenados = sorted(
        conflictos_en_rango, key=lambda x: obtener_prioridad(x["criterio"])
    )
    reservas_a_desplazar = []
    reservas_fijas = []
    for conflicto in conflictos_ordenados:
        prioridad_conflicto = obtener_prioridad(conflicto["criterio"])
        if prioridad_nueva < prioridad_conflicto:
            fecha_solicitud_conflicto = datetime.strptime(
                conflicto["fecha_reserva"], "%Y-%m-%d %H:%M:%S"
            )
            # Usar la hora local para la comparación de fechas
            fecha_actual = obtener_hora_local()
            if fecha_solicitud_conflicto.date() == fecha_actual.date():
                reservas_a_desplazar.append(conflicto)
            else:
                reservas_fijas.append(conflicto)
        elif prioridad_nueva == prioridad_conflicto:
            reservas_fijas.append(conflicto)
        else:
            reservas_fijas.append(conflicto)

    todas_reservas_fijas = [
        r for r in reservas_temporales if r not in reservas_a_desplazar
    ]
    horarios_con_fijas = encontrar_horarios_disponibles_en_rango(
        fecha,
        HORA_INICIO_DIA,
        HORA_FIN_DIA,
        todas_reservas_fijas,
        duracion_requerida_horas,
    )
    horarios_validos = []
    for inicio, fin in horarios_con_fijas:
        if verificar_solapamiento(inicio, fin, hora_inicio_rango, hora_fin_rango):
            horarios_validos.append((inicio, fin))

    if not horarios_validos:
        return False, reservas_existentes, None, []

    inicio_nuevo, fin_nuevo = horarios_validos[0]
    nueva_reserva["hora_inicio"] = inicio_nuevo
    nueva_reserva["hora_fin"] = fin_nuevo
    # --- CÁLCULO AUTOMÁTICO DE DURACIÓN ---
    duracion_calc = (time_to_minutes(fin_nuevo) - time_to_minutes(inicio_nuevo)) / 60.0
    nueva_reserva["duracion_horas"] = round(
        duracion_calc, 2
    )  # Asignar duración calculada
    # --- FIN CÁLCULO AUTOMÁTICO DE DURACIÓN ---
    reservas_reubicadas_exitosamente = []
    reservas_fallidas = []
    for reserva_desplazar in reservas_a_desplazar:
        # Usar la duración de la reserva a reubicar (asumida como 1.5 si no está)
        duracion_requerida_reubicar = reserva_desplazar.get("duracion_horas", 1.5)
        # Ajustar duracion_requerida_reubicar a 1, 2 o 3 horas si es necesario
        if duracion_requerida_reubicar >= 3:
            duracion_requerida_reubicar = 3
        elif duracion_requerida_reubicar >= 2:
            duracion_requerida_reubicar = 2
        elif duracion_requerida_reubicar >= 1:
            duracion_requerida_reubicar = 1
        else:
            duracion_requerida_reubicar = 1
        exito, nueva_reserva_desplazada = reubicar_reserva(
            reserva_desplazar,
            [r for r in todas_reservas_fijas if r["fecha"] == fecha] + [nueva_reserva],
            fecha,
            duracion_requerida_reubicar,
        )
        if exito:
            reservas_reubicadas_exitosamente.append(nueva_reserva_desplazada)
        else:
            reservas_fallidas.append(reserva_desplazar)

    if reservas_fallidas:
        return False, reservas_existentes, None, []

    reservas_finales = (
        todas_reservas_fijas + [nueva_reserva] + reservas_reubicadas_exitosamente
    )
    return (
        True,
        reservas_finales,
        (inicio_nuevo, fin_nuevo),
        reservas_reubicadas_exitosamente,
    )


# Funciones para métricas y gráficos (sin cambios o ligeramente adaptadas)
def calcular_metricas(reservas):
    if not reservas:
        return {
            "total_reservas": 0,
            "reservas_mes_actual": 0,
            "tasa_ocupacion": 0,
            "promedio_asistentes": 0,
            "reuniones_por_prioridad": {},
            "horas_totales_reservadas": 0,  # Añadido para métrica de duración
        }
    hoy = obtener_hora_local()  # <-- Cambiado a hora local
    mes_actual = hoy.month
    # Filtrar solo reservas que tienen una clave 'fecha' válida
    reservas_con_fecha = [r for r in reservas if "fecha" in r and r["fecha"]]
    reservas_mes = []
    for r in reservas_con_fecha:
        try:
            fecha_reserva = datetime.strptime(r["fecha"], "%Y-%m-%d")
            if fecha_reserva.month == mes_actual:
                reservas_mes.append(r)
        except ValueError:
            # Si la fecha no tiene el formato correcto, la ignora para el cálculo del mes
            print(
                f"Advertencia: Fecha inválida '{r['fecha']}' en reserva {r.get('id', 'desconocido')}, ignorando para métricas mensuales."
            )
            continue  # Saltar esta reserva para métricas mensuales

    # Calcular tasa de ocupación y horas totales (considerando duración)
    # Usamos 1.5 horas como duración por defecto para reservas antiguas
    horas_totales_mes = 9 * 5 * 4  # 180 horas disponibles estimadas
    horas_reservadas = sum(
        [r.get("duracion_horas", 1.5) for r in reservas_mes]
    )  # Sumar duración real o por defecto
    tasa_ocupacion = (
        (horas_reservadas / horas_totales_mes) * 100 if horas_totales_mes > 0 else 0
    )

    # Promedio de asistentes
    total_asistentes = sum([r.get("num_asistentes", 0) for r in reservas_con_fecha])
    promedio_asistentes = (
        total_asistentes / len(reservas_con_fecha) if reservas_con_fecha else 0
    )

    # Reuniones por prioridad
    reuniones_por_prioridad = {}
    for r in reservas_con_fecha:
        criterio = r["criterio"]
        reuniones_por_prioridad[criterio] = reuniones_por_prioridad.get(criterio, 0) + 1

    return {
        "total_reservas": len(reservas_con_fecha),  # Contar solo las que tienen fecha
        "reservas_mes_actual": len(reservas_mes),
        "tasa_ocupacion": round(tasa_ocupacion, 1),
        "promedio_asistentes": round(promedio_asistentes, 1),
        "reuniones_por_prioridad": reuniones_por_prioridad,
        "horas_totales_reservadas": horas_reservadas,  # Añadido
    }


def crear_grafico_ocupacion_semanal(reservas):
    if not reservas:
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles", showarrow=False, font_size=16
        )
        return fig
    # Agrupar por día de la semana, solo con fechas válidas
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
    conteo_dias = {dia: 0 for dia in dias_semana}
    for r in reservas:
        if "fecha" in r and r["fecha"]:
            try:
                fecha = datetime.strptime(r["fecha"], "%Y-%m-%d")
                if fecha.weekday() < 5:
                    dia_nombre = dias_semana[fecha.weekday()]
                    conteo_dias[dia_nombre] += 1
            except ValueError:
                print(
                    f"Advertencia: Fecha inválida '{r['fecha']}' en reserva {r.get('id', 'desconocido')}, ignorando para gráfico semanal."
                )
                continue  # Saltar esta reserva
    fig = go.Figure(
        data=[
            go.Bar(
                x=list(conteo_dias.keys()),
                y=list(conteo_dias.values()),
                marker_color=["#667eea", "#764ba2", "#f093fb", "#4facfe", "#43e97b"],
                text=list(conteo_dias.values()),
                textposition="outside",
            )
        ]
    )
    fig.update_layout(
        title="Distribución de Reuniones por Día de la Semana",
        xaxis_title="Día",
        yaxis_title="Número de Reuniones",
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif"),
    )
    return fig


def crear_grafico_prioridades(metricas):
    if not metricas["reuniones_por_prioridad"]:
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles", showarrow=False, font_size=16
        )
        return fig
    labels = list(metricas["reuniones_por_prioridad"].keys())
    values = list(metricas["reuniones_por_prioridad"].values())
    colors = ["#ef4444", "#f59e0b", "#3b82f6", "#6b7280"]
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker_colors=colors,
                textinfo="label+percent",
                textposition="outside",
            )
        ]
    )
    fig.update_layout(
        title="Distribución por Criterio de Prioridad",
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif"),
        showlegend=True,
    )
    return fig


def crear_grafico_tendencia_mensual(reservas):
    if not reservas:
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles", showarrow=False, font_size=16
        )
        return fig
    # Agrupar por mes, solo con fechas válidas
    reservas_por_mes = {}
    for r in reservas:
        if "fecha" in r and r["fecha"]:
            try:
                fecha = datetime.strptime(r["fecha"], "%Y-%m-%d")
                mes_año = fecha.strftime("%Y-%m")
                reservas_por_mes[mes_año] = reservas_por_mes.get(mes_año, 0) + 1
            except ValueError:
                print(
                    f"Advertencia: Fecha inválida '{r['fecha']}' en reserva {r.get('id', 'desconocido')}, ignorando para gráfico mensual."
                )
                continue  # Saltar esta reserva
    meses = sorted(reservas_por_mes.keys())
    valores = [reservas_por_mes[m] for m in meses]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=meses,
            y=valores,
            mode="lines+markers",
            name="Reservas",
            line=dict(color="#667eea", width=3),
            marker=dict(size=10, color="#764ba2"),
            fill="tozeroy",
            fillcolor="rgba(102, 126, 234, 0.1)",
        )
    )
    fig.update_layout(
        title="Tendencia de Reservas Mensuales",
        xaxis_title="Mes",
        yaxis_title="Número de Reservas",
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif"),
    )
    return fig


def crear_mapa_calor_horarios(reservas):
    if not reservas:
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles", showarrow=False, font_size=16
        )
        return fig
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
    horas = [f"{h:02d}:00" for h in range(8, 17)]
    matriz = [[0 for _ in range(len(horas))] for _ in range(len(dias))]
    for r in reservas:
        if "fecha" in r and r["fecha"] and "hora_inicio" in r and r["hora_inicio"]:
            try:
                fecha = datetime.strptime(r["fecha"], "%Y-%m-%d")
                if fecha.weekday() < 5:
                    dia_idx = fecha.weekday()
                    hora_inicio = datetime.strptime(r["hora_inicio"], "%H:%M").hour
                    if 8 <= hora_inicio < 17:
                        hora_idx = hora_inicio - 8
                        matriz[dia_idx][hora_idx] += 1
            except ValueError:
                print(
                    f"Advertencia: Fecha u hora inválida en reserva {r.get('id', 'desconocido')}: fecha='{r.get('fecha')}', hora_inicio='{r.get('hora_inicio')}', ignorando para mapa de calor."
                )
                continue  # Saltar esta reserva
    fig = go.Figure(
        data=go.Heatmap(
            z=matriz,
            x=horas,
            y=dias,
            colorscale="Purples",
            text=matriz,
            texttemplate="%{text}",
            textfont={"size": 10},
            colorbar=dict(title="Reuniones"),
        )
    )
    fig.update_layout(
        title="Mapa de Calor: Horarios Más Solicitados",
        xaxis_title="Hora",
        yaxis_title="Día",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(family="Inter, sans-serif"),
    )
    return fig


# Inicializar reservas (ahora desde Google Sheets)
if "reservas" not in st.session_state:
    st.session_state.reservas = cargar_reservas()
# Navegación por pestañas
tab1, tab2, tab3 = st.tabs(
    ["📊 Dashboard", "📝 Nueva Reserva", "📋 Gestión de Reservas"]
)
with tab1:
    cols1, cols2 = st.columns([2, 6])
    with cols1:
        logo2 = load_logo("CESFAM.jpg")  # Asegúrate de que la ruta sea correcta
        st.image(logo2)
    with cols2:
        # Header principal
        st.markdown(
            """
        <div class="main-header">
            <h1>🏢 Sistema de Reserva</h1>
            <p>Gestión Inteligente con Análisis de Datos en Tiempo Real</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    # Calcular métricas
    metricas = calcular_metricas(st.session_state.reservas)
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
        <div class="metric-card">
            <p class="metric-value">{metricas["total_reservas"]}</p>
            <p class="metric-label">Total Reservas</p>
            <p class="metric-delta">↑ Sistema activo</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
        <div class="metric-card" style="border-left-color: #10b981;">
            <p class="metric-value" style="color: #10b981;">{metricas["reservas_mes_actual"]}</p>
            <p class="metric-label">Este Mes</p>
            <p class="metric-delta">↑ Mes actual</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
        <div class="metric-card" style="border-left-color: #f59e0b;">
            <p class="metric-value" style="color: #f59e0b;">{metricas["tasa_ocupacion"]}%</p>
            <p class="metric-label">Tasa Ocupación</p>
            <p class="metric-delta">↑ Óptimo uso</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
        <div class="metric-card" style="border-left-color: #3b82f6;">
            <p class="metric-value" style="color: #3b82f6;">{metricas["promedio_asistentes"]}</p>
            <p class="metric-label">Promedio Asistentes</p>
            <p class="metric-delta">↑ Por reunión</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    # Gráficos
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.plotly_chart(
            crear_grafico_ocupacion_semanal(st.session_state.reservas),
            use_container_width=True,
            key="grafico_ocupacion_semanal",
        )
    with col_g2:
        st.plotly_chart(
            crear_grafico_prioridades(metricas),
            use_container_width=True,
            key="grafico_prioridades",
        )
    # Segunda fila de gráficos
    col_g3, col_g4 = st.columns(2)
    with col_g3:
        st.plotly_chart(
            crear_grafico_tendencia_mensual(st.session_state.reservas),
            use_container_width=True,
            key="grafico_tendencia_mensual",
        )
    with col_g4:
        # Gráfico de asistentes promedio por criterio
        if st.session_state.reservas:
            # Filtrar reservas con fecha válida para este gráfico también
            reservas_con_fecha = [
                r for r in st.session_state.reservas if "fecha" in r and r["fecha"]
            ]
            if reservas_con_fecha:
                df_asistentes = pd.DataFrame(reservas_con_fecha)
                asistentes_por_criterio = (
                    df_asistentes.groupby("criterio")["num_asistentes"]
                    .mean()
                    .reset_index()
                )
                fig = go.Figure(
                    data=[
                        go.Bar(
                            x=asistentes_por_criterio["criterio"],
                            y=asistentes_por_criterio["num_asistentes"],
                            marker_color="#667eea",
                            text=asistentes_por_criterio["num_asistentes"].round(1),
                            textposition="outside",
                        )
                    ]
                )
                fig.update_layout(
                    title="Promedio de Asistentes por Criterio",
                    xaxis_title="Criterio",
                    yaxis_title="Promedio de Asistentes",
                    height=350,
                    margin=dict(l=20, r=20, t=40, b=20),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter, sans-serif"),
                )
                st.plotly_chart(
                    fig, use_container_width=True, key="grafico_asistentes_criterio"
                )
            else:
                st.info(
                    "📊 No hay datos con fecha válida suficientes para mostrar este gráfico"
                )
        else:
            st.info("📊 No hay datos suficientes para mostrar este gráfico")
    # Mapa de calor completo
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    st.plotly_chart(
        crear_mapa_calor_horarios(st.session_state.reservas),
        use_container_width=True,
        key="mapa_calor_horarios",
    )
    # Información adicional
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.markdown(
            """
        <div class="info-box">
            <h4>⏰ Horario de Operación</h4>
            <p><strong>08:00 - 17:00</strong></p>
            <p>Lunes a Viernes</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col_info2:
        st.markdown(
            """
        <div class="success-box">
            <h4>✅ Sistema Activo</h4>
            <p><strong>Gestión automática</strong></p>
            <p>Reubicación inteligente</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col_info3:
        st.markdown(
            """
        <div class="warning-box">
            <h4>📋 Plazos</h4>
            <p><strong>1-2 días hábiles</strong></p>
            <p>Según prioridad</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
with tab2:
    st.markdown(
        """
    <div class="main-header">
        <h1>📝 Nueva Reserva</h1>
        <p>Complete el formulario para solicitar una sala de reuniones</p>
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 👤 Información del Solicitante")
        nombre = st.text_input(
            "Nombre completo *", key="nombre", placeholder="Ej: Juan Pérez"
        )
        email = st.text_input(
            "Correo electrónico *", key="email", placeholder="ejemplo@empresa.cl"
        )
        st.markdown("### 📅 Detalles de la Reunión")
        fecha = st.date_input(
            "Fecha de la reunión *",
            min_value=datetime.today().date() + timedelta(days=1),
            key="fecha",
        )
        fecha_str = fecha.strftime("%Y-%m-%d")
        criterio = st.selectbox(
            "Criterio de prioridad *",
            options=[
                "",
                "1 - Supervisión de Referentes",
                "2 - Reuniones con la Comunidad",
                "3 - Reuniones de Equipos",
                "4 - Reuniones Generales (mínimo 4 personas)",
            ],
            key="criterio",
            help="Seleccione el criterio según la importancia de su reunión",
        )
        # Mostrar badge de prioridad
        if criterio:
            prioridad_num = criterio[0]
            st.markdown(
                f'<span class="priority-badge priority-{prioridad_num}">Prioridad {prioridad_num}</span>',
                unsafe_allow_html=True,
            )
    with col2:
        st.markdown("### 🕐 Horario Preferido")
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            # Mantener la línea original sin min_value ni max_value
            hora_inicio_rango = st.time_input(
                "Inicio preferido *", value=time(9, 0), key="inicio_rango"
            )
        with col_h2:
            # Mantener la línea original sin min_value ni max_value
            hora_fin_rango = st.time_input(
                "Fin preferido *", value=time(16, 0), key="fin_rango"
            )

        # --- ELIMINAR SELECCIÓN DE DURACIÓN ---
        # No se muestra el selectbox de duración
        # Calcular la duración del rango seleccionado
        duracion_rango_minutos = time_to_minutes(hora_fin_rango) - time_to_minutes(
            hora_inicio_rango
        )
        duracion_rango_horas = duracion_rango_minutos / 60.0
        st.info(f"💡 Duración del rango seleccionado: {duracion_rango_horas:.2f} horas")

        st.markdown("### 👥 Información Adicional")
        num_asistentes = st.number_input(
            "Número de asistentes *",
            min_value=1,
            max_value=20,
            value=4,
            key="asistentes",
            help="Indique cuántas personas asistirán",
        )
        proposito = st.text_area(
            "Propósito de la reunión *",
            height=120,
            key="proposito",
            placeholder="Describa brevemente el objetivo de la reunión...",
        )
    st.markdown("</div>", unsafe_allow_html=True)
    # Validar rango horario
    rango_valido = True
    # Ajustar la validación para permitir rangos de al menos 1 hora
    duracion_minima_requerida = 1 * 60  # 1 hora en minutos
    duracion_rango_minutos = time_to_minutes(hora_fin_rango) - time_to_minutes(
        hora_inicio_rango
    )
    if hora_inicio_rango >= hora_fin_rango:
        st.error("❌ La hora de inicio debe ser anterior a la hora de fin")
        rango_valido = False
    elif duracion_rango_minutos < duracion_minima_requerida:
        st.error(f"❌ El rango horario debe permitir al menos 1 hora de reunión")
        rango_valido = False
    elif hora_inicio_rango < HORA_INICIO_DIA or hora_fin_rango > HORA_FIN_DIA:
        st.error(
            f"❌ El rango horario debe estar entre {HORA_INICIO_DIA.strftime('%H:%M')} y {HORA_FIN_DIA.strftime('%H:%M')}"
        )
        rango_valido = False
    # Botón de reserva
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("✅ Confirmar Reserva", type="primary", use_container_width=True):
            # Validaciones
            errores = []
            if not nombre.strip():
                errores.append("❌ El nombre es obligatorio")
            if not email.strip() or "@" not in email:
                errores.append("❌ El correo electrónico es inválido")
            if not criterio:
                errores.append("❌ Debe seleccionar un criterio de prioridad")
            if not proposito.strip():
                errores.append("❌ El propósito de la reunión es obligatorio")
            if not rango_valido:
                errores.append("❌ El rango horario no es válido")
            if criterio.startswith("4") and num_asistentes < 4:
                errores.append(
                    "❌ Las reuniones generales deben tener mínimo 4 personas"
                )
            if criterio:
                plazo_valido, mensaje_plazo = validar_plazo_reserva(fecha, criterio)
                if not plazo_valido:
                    errores.append(f"❌ {mensaje_plazo}")
            # Mostrar errores
            if errores:
                for error in errores:
                    st.error(error)
            else:
                # Crear nueva reserva
                nueva_reserva = {
                    "nombre": nombre.strip(),
                    "email": email.strip(),
                    "fecha": fecha_str,
                    "hora_inicio_rango": hora_inicio_rango.strftime("%H:%M"),
                    "hora_fin_rango": hora_fin_rango.strftime("%H:%M"),
                    "hora_inicio": "",
                    "hora_fin": "",
                    "criterio": criterio,
                    "num_asistentes": int(num_asistentes),
                    "proposito": proposito.strip(),
                    "fecha_reserva": obtener_hora_local().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),  # <-- Cambiado a hora local
                    # No se incluye 'duracion_horas' aquí, se calculará después
                }
                # --- GENERAR ID ÚNICO ANTES DEL PROCESAMIENTO ---
                # Cargar la lista de reservas *antes* de procesar para calcular el ID
                id_unica = generar_id_unica_para_fecha(fecha_str)
                nueva_reserva["id"] = id_unica
                print(f"ID generado antes del procesamiento: {id_unica}")
                # --- FIN GENERAR ID ÚNICO ---
                # Procesar reserva
                exito, reservas_actualizadas, horario_asignado, reservas_reubicadas = (
                    procesar_reserva_con_rango_y_prioridad(
                        nueva_reserva, st.session_state.reservas
                    )
                )
                if exito:
                    # Asignar horario a la nueva_reserva original (ya tiene el ID)
                    nueva_reserva["hora_inicio"] = horario_asignado[0]
                    nueva_reserva["hora_fin"] = horario_asignado[1]
                    # La duración ya fue calculada y asignada en procesar_reserva_con_rango_y_prioridad
                    duracion_calculada = nueva_reserva["duracion_horas"]
                    # Guardar la reserva en Google Sheets (el ID ya está asignado)
                    # Importante: Quitar 'duracion_horas' antes de guardar
                    reserva_a_guardar = nueva_reserva.copy()
                    del reserva_a_guardar["duracion_horas"]
                    record_id = guardar_reserva(reserva_a_guardar)
                    if record_id:
                        # El ID ya está en nueva_reserva, no es necesario asignarlo de nuevo aquí
                        # --- CORRECCIÓN AQUÍ ---
                        # Actualizar la lista principal (reservas) con la lista procesada
                        # para que coincida con la lista procesada y guardada
                        # Asegurarse de que las reservas en la lista tengan 'duracion_horas' para la lógica interna
                        st.session_state.reservas = []
                        for r_proc in reservas_actualizadas:
                            r_proc_id = r_proc.get("id", "")
                            # El ID ya debería estar presente si se generó antes del procesamiento
                            # y se mantuvo en la reserva original y en las reubicadas si existen.
                            # Si alguna reserva temporal (durante el proceso) no tiene ID,
                            # se intenta encontrarla o asignarle el ID original.
                            if not r_proc_id:  # Si no tiene ID, buscarlo o asignarlo
                                # Buscar en DB si ya fue guardado y tiene ID
                                for r_db in st.session_state.get("reservas_db", []):
                                    if (
                                        r_proc.get("fecha") == r_db.get("fecha")
                                        and r_proc.get("hora_inicio")
                                        == r_db.get("hora_inicio")
                                        and r_proc.get("nombre") == r_db.get("nombre")
                                        and r_proc.get("email") == r_db.get("email")
                                    ):
                                        r_proc["id"] = r_db["id"]
                                        print(
                                            f"Asignando ID {r_db['id']} a reserva sin ID durante actualización: {r_proc}"
                                        )
                                        break
                                # Si aún no tiene ID, y es la nueva reserva, usar el ID generado
                                if "id" not in r_proc or not r_proc["id"]:
                                    if (
                                        r_proc.get("fecha") == nueva_reserva["fecha"]
                                        and r_proc.get("nombre")
                                        == nueva_reserva["nombre"]
                                        and r_proc.get("email")
                                        == nueva_reserva["email"]
                                    ):
                                        r_proc["id"] = nueva_reserva[
                                            "id"
                                        ]  # Asignar ID de la nueva reserva
                                        print(
                                            f"Asignando ID original {nueva_reserva['id']} a la nueva reserva procesada: {r_proc}"
                                        )
                            # Asegurar que 'duracion_horas' esté presente para la lógica futura
                            if "duracion_horas" not in r_proc:
                                r_proc["duracion_horas"] = (
                                    1.5  # Asignar valor por defecto si no está
                                )
                            st.session_state.reservas.append(r_proc)
                        # Mensaje de éxito
                        st.markdown(
                            """
                        <div class="success-box">
                            <h3>🎉 ¡Reserva Confirmada!</h3>
                            <p>Su sala ha sido reservada exitosamente</p>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                        st.balloons()
                        # Detalles de la reserva
                        col_d1, col_d2 = st.columns(2)
                        with col_d1:
                            st.markdown("### 📋 Detalles de su Reserva")
                            st.write(f"**📅 Fecha:** {fecha_str}")
                            st.write(
                                f"**🕐 Horario:** {horario_asignado[0]} - {horario_asignado[1]}"
                            )
                            st.write(
                                f"**⏱️ Duración calculada:** {duracion_calculada} hora(s)"
                            )  # Mostrar duración calculada
                            st.write(f"**🏷️ Criterio:** {criterio}")
                            st.write(f"**👥 Asistentes:** {num_asistentes}")
                        with col_d2:
                            st.markdown("### 📧 Confirmación")
                            st.write(f"**📧 Email:** {email}")
                            st.write(f"**🔑 ID:** {record_id}")
                            st.write(
                                f"**📅 Solicitado:** {obtener_hora_local().strftime('%d/%m/%Y %H:%M')}"
                            )  # <-- Cambiado a hora local
                            st.write(
                                f"**📝 Rango:** {hora_inicio_rango.strftime('%H:%M')} - {hora_fin_rango.strftime('%H:%M')}"
                            )
                        if reservas_reubicadas:
                            st.markdown(
                                """
                            <div class="info-box">
                                <h4>🔄 Reuniones Reubicadas</h4>
                                <p><strong>{}</strong> reunión(es) de menor prioridad fueron reubicadas automáticamente</p>
                                <p style="font-size: 0.9rem; opacity: 0.9;">Solo se reubican reservas del mismo día</p>
                            </div>
                            """.format(len(reservas_reubicadas)),
                                unsafe_allow_html=True,
                            )
                    else:
                        st.error("❌ Error al guardar la reserva en Google Sheets.")
                else:
                    st.error(
                        "❌ No se pudo asignar un horario. No hay disponibilidad en el rango solicitado."
                    )
with tab3:
    st.markdown(
        """
    <div class="main-header">
        <h1>📋 Gestión de Reservas</h1>
        <p>Visualice y administre todas las reservas programadas</p>
    </div>
    """,
        unsafe_allow_html=True,
    )
    # Botón de actualización
    col_act1, col_act2, col_act3 = st.columns([1, 1, 1])
    with col_act2:
        if st.button("🔄 Actualizar Lista", use_container_width=True):
            # Recargar la lista desde Google Sheets
            st.session_state.reservas = cargar_reservas()
            st.success("✅ Lista actualizada correctamente")
    # Filtros
    st.markdown("### 🔍 Filtros")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filtro_criterio = st.multiselect(
            "Filtrar por criterio", options=list(CRITERIO_PRIORIDAD.keys()), default=[]
        )
    with col_f2:
        fecha_desde = st.date_input(
            "Desde", value=obtener_hora_local().date()
        )  # <-- Cambiado a hora local
    with col_f3:
        fecha_hasta = st.date_input(
            "Hasta", value=obtener_hora_local().date() + timedelta(days=30)
        )  # <-- Cambiado a hora local
    # --- NUEVO: Pestañas para Lista, Vista Tipo Calendario y Calendario Visual ---
    view_tab1, view_tab2, view_tab3 = st.tabs(
        ["📋 Lista de Reservas", "📅 Vista Tipo Calendario", "📆 Calendario Visual"]
    )
    with view_tab1:  # Contenido original de la lista
        # Obtener reservas futuras basadas en los filtros
        reservas_futuras = []
        for reserva in st.session_state.reservas:
            # Asegurarse de que la reserva tiene la clave 'fecha'
            if "fecha" not in reserva:
                print(f"Advertencia: Reserva sin clave 'fecha': {reserva}")
                continue  # Saltar esta reserva
            try:
                fecha_reserva = datetime.strptime(reserva["fecha"], "%Y-%m-%d").date()
                # Aplicar filtros
                if fecha_reserva < fecha_desde or fecha_reserva > fecha_hasta:
                    continue
                if filtro_criterio and reserva["criterio"] not in filtro_criterio:
                    continue
                reservas_futuras.append(reserva)
            except ValueError:
                print(
                    f"Advertencia: Fecha inválida '{reserva['fecha']}' en reserva {reserva.get('id', 'desconocido')}, ignorando filtro."
                )
                continue  # Saltar esta reserva si la fecha es inválida
        if reservas_futuras:
            # Agregar prioridad numérica
            for reserva in reservas_futuras:
                reserva["prioridad_num"] = obtener_prioridad(reserva["criterio"])
            df_reservas = pd.DataFrame(reservas_futuras)
            df_reservas = df_reservas.sort_values(
                ["fecha", "prioridad_num", "hora_inicio"]
            )
            # Mostrar estadísticas del filtro
            col_est1, col_est2, col_est3, col_est4 = st.columns(4)
            with col_est1:
                st.metric("📊 Total Reservas", len(reservas_futuras))
            with col_est2:
                total_asistentes = df_reservas["num_asistentes"].sum()
                st.metric("👥 Total Asistentes", int(total_asistentes))
            with col_est3:
                dias_unicos = df_reservas["fecha"].nunique()
                st.metric("📅 Días Ocupados", dias_unicos)
            with col_est4:
                prioridad_alta = len(df_reservas[df_reservas["prioridad_num"] <= 2])
                st.metric("⭐ Alta Prioridad", prioridad_alta)
            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
            # Tabla de reservas con diseño mejorado
            st.markdown("### 📊 Lista de Reservas")
            # Quitar 'duracion_horas' de la visualización en la tabla
            columnas_mostrar = [
                "id",
                "fecha",
                "hora_inicio",
                "hora_fin",
                "nombre",
                "email",
                "criterio",
                "num_asistentes",
                "proposito",
            ]
            df_display = df_reservas[columnas_mostrar].copy()
            df_display.columns = [
                "ID",
                "Fecha",
                "Inicio",
                "Fin",
                "Nombre",
                "Email",
                "Criterio",
                "Asistentes",
                "Propósito",
            ]
            # Formatear propósito
            df_display["Propósito"] = df_display["Propósito"].apply(
                lambda x: x[:50] + "..." if len(str(x)) > 50 else x
            )
            # Formatear fecha
            df_display["Fecha"] = pd.to_datetime(
                df_display["Fecha"], errors="coerce"
            ).dt.strftime("%d/%m/%Y")
            # Mostrar tabla con formato
            st.dataframe(
                df_display, use_container_width=True, height=400, hide_index=True
            )
            # Opción de descarga
            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
            csv = df_display.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Descargar Reservas (CSV)",
                data=csv,
                file_name=f"reservas_{obtener_hora_local().strftime('%Y%m%d')}.csv",  # <-- Cambiado a hora local
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.markdown(
                """
            <div class="info-box">
                <h3>📭 No hay reservas</h3>
                <p>No se encontraron reservas con los filtros aplicados</p>
            </div>
            """,
                unsafe_allow_html=True,
            )
    with view_tab2:  # Nueva pestaña para una Vista tipo Calendario alternativa
        st.markdown("### 📅 Vista Tipo Calendario")

        # --- Selector de Mes para el Calendario de Calor ---
        # Definir nombres de meses en español
        nombres_meses_es = [
            "Enero",
            "Febrero",
            "Marzo",
            "Abril",
            "Mayo",
            "Junio",
            "Julio",
            "Agosto",
            "Septiembre",
            "Octubre",
            "Noviembre",
            "Diciembre",
        ]

        # Usamos la hora local para determinar el mes/ año por defecto
        hoy_local = obtener_hora_local().date()

        # Selector para elegir el mes y año a visualizar
        col_mes, col_anio, _ = st.columns([2, 2, 4])  # Dar espacio extra al final
        with col_mes:
            # Usar índice para seleccionar el mes por defecto (1-12 -> 0-11)
            mes_seleccionado = st.selectbox(
                "Seleccionar Mes",
                options=list(range(1, 13)),  # Valores 1 a 12
                format_func=lambda x: nombres_meses_es[
                    x - 1
                ],  # Mapear 1->Enero, ..., 12->Diciembre
                index=hoy_local.month
                - 1,  # Por defecto, el mes actual (ajustar índice 0-based)
                key="cal_selector_mes",
            )
        with col_anio:
            anio_seleccionado = st.number_input(
                "Seleccionar Año",
                min_value=2020,
                max_value=2030,
                value=hoy_local.year,  # Por defecto, el año actual
                step=1,
                key="cal_selector_anio",
            )
        # --- Fin Selector de Mes ---

        # --- Generar Datos para el Calendario de Calor del Mes Seleccionado ---
        # 1. Filtrar reservas por el mes y año seleccionados
        reservas_mes_seleccionado = []
        for r in st.session_state.reservas:
            if "fecha" in r and r["fecha"]:
                try:
                    fecha_reserva = datetime.strptime(r["fecha"], "%Y-%m-%d").date()
                    # Aplicar filtro de mes y año seleccionados
                    if (
                        fecha_reserva.year == anio_seleccionado
                        and fecha_reserva.month == mes_seleccionado
                    ):
                        # Aplicar también el filtro de criterio global de la pestaña
                        if not filtro_criterio or r["criterio"] in filtro_criterio:
                            reservas_mes_seleccionado.append(r)
                except ValueError:
                    continue  # Ignorar fechas inválidas

        # 2. Contar reuniones por día
        conteo_dias = {}
        if reservas_mes_seleccionado:
            for r in reservas_mes_seleccionado:
                fecha_str = r["fecha"]
                conteo_dias[fecha_str] = conteo_dias.get(fecha_str, 0) + 1

        # --- Fin Generación de Datos ---

        # --- Mostrar Calendario de Calor Mensual ---
        if conteo_dias:
            # Crear una lista de tuplas (fecha_str, count) y ordenarla por fecha
            datos_ordenados = sorted(conteo_dias.items())
            fechas_plot = [item[0] for item in datos_ordenados]
            conteos_plot = [item[1] for item in datos_ordenados]

            # Crear el gráfico de barras con Plotly
            fig_calendario = go.Figure(
                data=go.Bar(
                    x=fechas_plot,
                    y=conteos_plot,
                    marker_color="#667eea",
                    text=conteos_plot,
                    textposition="outside",
                )
            )

            # Configurar el layout del gráfico
            # Obtener el nombre del mes en español usando el índice
            nombre_mes = nombres_meses_es[mes_seleccionado - 1]
            fig_calendario.update_layout(
                title=f"Reuniones en {nombre_mes} {anio_seleccionado}",
                xaxis_title="Fecha",
                yaxis_title="Número de Reuniones",
                height=400,
                margin=dict(l=20, r=20, t=40, b=20),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif"),
            )
            # Mostrar el gráfico
            st.plotly_chart(
                fig_calendario,
                use_container_width=True,
                key=f"calendario_calor_{mes_seleccionado}_{anio_seleccionado}",
            )

            # Mostrar lista resumida de eventos en ese día si se hace clic (opcional, simplificado)
            # Aquí simplemente mostramos la lista completa filtrada por mes
            st.markdown(f"#### 📋 Reuniones en {nombre_mes} {anio_seleccionado}")
            # Reutilizamos la lógica de la tabla pero solo para el mes seleccionado
            df_reservas_mes = pd.DataFrame(reservas_mes_seleccionado)
            # Agregar prioridad numérica para ordenar
            df_reservas_mes["prioridad_num"] = df_reservas_mes["criterio"].map(
                obtener_prioridad
            )
            df_reservas_mes = df_reservas_mes.sort_values(
                ["fecha", "prioridad_num", "hora_inicio"]
            )

            # Columnas a mostrar (quitando duracion_horas si se desea)
            columnas_mostrar_cal = [
                "id",
                "fecha",
                "hora_inicio",
                "hora_fin",
                "nombre",
                "email",
                "criterio",
                "num_asistentes",
            ]
            df_display_cal = df_reservas_mes[columnas_mostrar_cal].copy()
            df_display_cal.columns = [
                "ID",
                "Fecha",
                "Inicio",
                "Fin",
                "Nombre",
                "Email",
                "Criterio",
                "Asistentes",
            ]

            # Formatear fechas
            df_display_cal["Fecha"] = pd.to_datetime(
                df_display_cal["Fecha"]
            ).dt.strftime("%d/%m/%Y")

            st.dataframe(df_display_cal, use_container_width=True, hide_index=True)

        else:
            # Obtener el nombre del mes en español para el mensaje
            nombre_mes = nombres_meses_es[mes_seleccionado - 1]
            st.info(
                f"ℹ️ No se encontraron reservas para {nombre_mes} de {anio_seleccionado} con los criterios seleccionados."
            )

# --- Fin Mostrar Calendario de Calor ---

with view_tab3:
    # =====================================================
    # VISTA 3: CALENDARIO VISUAL INTERACTIVO
    # =====================================================
    st.markdown("### 📆 Calendario Visual")

    with st.expander("Ver Calendario", expanded=True):
        # Filtrar reservas para el calendario usando los mismos filtros
        reservas_calendario = []
        for reserva in st.session_state.reservas:
            if "fecha" not in reserva:
                continue
            try:
                fecha_reserva = datetime.strptime(reserva["fecha"], "%Y-%m-%d").date()
                if fecha_reserva < fecha_desde or fecha_reserva > fecha_hasta:
                    continue
                if filtro_criterio and reserva["criterio"] not in filtro_criterio:
                    continue
                reservas_calendario.append(reserva)
            except ValueError:
                continue

            if reservas_calendario:
                df_calendario = pd.DataFrame(reservas_calendario)

                # Convertir reservas a eventos para el calendario
                eventos = []
                for _, reserva in df_calendario.iterrows():
                    eventos.append(
                        {
                            "title": f"{reserva['nombre']} ({reserva['hora_inicio']} - {reserva['hora_fin']})",
                            "start": f"{reserva['fecha']}T{reserva['hora_inicio']}",
                            "end": f"{reserva['fecha']}T{reserva['hora_fin']}",
                            "backgroundColor": obtener_color_prioridad(
                                reserva["criterio"]
                            ),
                            "borderColor": obtener_color_prioridad(reserva["criterio"]),
                        }
                    )

                # Configuración del calendario
                calendar_options = {
                    "initialView": "dayGridMonth",
                    "headerToolbar": {
                        "left": "prev,next today",
                        "center": "title",
                        "right": "dayGridMonth,timeGridWeek,listWeek",
                    },
                    "editable": False,
                    "height": "600px",
                    "locale": "es",
                }

                # Mostrar el calendario
                calendar_value = calendar(
                    events=eventos, options=calendar_options, key="calendar_view"
                )

                # Leyenda de colores
                st.markdown("""
                **Leyenda de colores:**
                - 🔴 Supervisión de Referentes (Máxima prioridad)
                - 🟠 Reuniones con la Comunidad (Alta prioridad)
                - 🟡 Reuniones de Equipos (Media prioridad)
                - 🟢 Reuniones Generales (Baja prioridad)
                """)
            else:
                st.info(
                    "ℹ️ No hay reservas con los filtros aplicados para mostrar en el calendario."
                )

# Sidebar con información y carga de logo
with st.sidebar:
    st.markdown(
        """
    <div style='text-align: center; padding: 1rem;'>
        <h2 style='color: #667eea;'>🏢 Sistema de Reservas</h2>
        <p style='color: #666; font-size: 0.9rem;'>Versión 2.0 Professional</p>
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("### 📋 Guía Rápida")
    with st.expander("🕐 Horarios"):
        st.markdown("""
        - **Operación:** 08:00 - 17:00
        - **Días:** Lunes a Viernes
        - **Duración:** Calculada como la diferencia entre horario de inicio y fin asignado.
        - **Bloques:** Cada 30 minutos
        """)
    with st.expander("📅 Plazos de Reserva"):
        st.markdown("""
        **Alta Prioridad (1-2):**
        - Mínimo 1 día hábil
        **Prioridad Normal (3-4):**
        - Mínimo 2 días hábiles
        """)
    with st.expander("🥇 Criterios de Prioridad"):
        st.markdown("""
        1. **Supervisión** - Máxima
        2. **Comunidad** - Alta
        3. **Equipos** - Media
        4. **General** - Baja (mín. 4 personas)
        """)
    with st.expander("⚖️ Política de Reubicación"):
        st.markdown("""
        - Solo reservas del **mismo día**
        - Respeto a **mayor prioridad**
        - Confirmadas **no se modifican**
        - Sistema **automático**
        """)
    st.markdown("---")
    # Información del sistema
    st.markdown("### ℹ️ Estado del Sistema")
    st.success("🟢 Sistema Operativo")
    hora_actual_local = obtener_hora_local()  # <-- Cambiado a hora local
    st.info(f"📅 {hora_actual_local.strftime('%d/%m/%Y %H:%M')}")
    st.caption(f"Total de reservas: {len(st.session_state.reservas)}")
# Footer
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
st.markdown(
    """
<div style='text-align: center; color: #666; padding: 2rem; background: #f8f9fa; border-radius: 10px;'>
    <p style='margin: 0; font-size: 0.9rem;'>
        <strong>Sistema de Reserva de Salas - Gestión Inteligente</strong><br>
        Almacenamiento en Google Sheets | IDs Categorizados | Análisis en tiempo real<br>
        <span style='font-size: 0.8rem;'>Desarrollado usando Streamlit y Plotly</span>
    </p>
</div>
""",
    unsafe_allow_html=True,
)
# Añadir pie de página adicional con logo y contacto
with st.container():
    col1, col2, col3, col4 = st.columns([3, 1, 5, 1])
    with col2:
        try:
            logo = load_logo("logo_alain.png")  # Asegúrate de que la ruta sea correcta
            st.image(logo, width=150)
        except FileNotFoundError:
            st.warning("Logo no encontrado en 'logo_alain.png'")
    with col3:
        st.markdown(
            """
                <div style='text-align: left; color: #888888; font-size: 20px; padding-bottom: 20px;'>
                    💼 Aplicación desarrollada por <strong>Alain Antinao Sepúlveda</strong> <br>
                    📧 Contacto: <a href="mailto:alain.antinao.s@gmail.com" style="color: #4A90E2;">alain.antinao.s@gmail.com</a> <br>
                    🌐 Más información en: <a href="https://alain-antinao-s.notion.site/Alain-C-sar-Antinao-Sep-lveda-1d20a081d9a980ca9d43e283a278053e" target="_blank" style="color: #4A90E2;">Mi página personal</a>
                </div>
            """,
            unsafe_allow_html=True,
        )
