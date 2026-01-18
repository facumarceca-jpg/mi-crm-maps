import streamlit as st
import pandas as pd
import os
import re
import pydeck as pdk
import json
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Helper for layout
def make_clickable_card(title, value, key):
    return st.button(f"{title}\n\n**{value}**", key=key, use_container_width=True)

# Custom CSS for SaaS Look
def local_css():
    st.markdown("""
        <style>
        /* Red Theme Background */
        [data-testid="stAppViewRoot"], .stApp {
            background-color: #FF4B4B !important; /* Streamlit Red */
            color: #ffffff !important;
        }
        /* Style for headers and normal text to be white for contrast on red */
        h1, h2, h3, h4, p, span, label, div {
            color: #ffffff !important;
            font-weight: 500 !important;
        }
        /* Buttons should be black or white for high contrast */
        button[kind="primary"], button[kind="secondary"] {
            background-color: #000000 !important;
            color: #ffffff !important;
            border: 1px solid #ffffff !important;
            min-height: 52px !important;
        }
        /* Notifications/Info boxes inside the red background */
        [data-testid="stNotification"] {
            background-color: rgba(255, 255, 255, 0.9) !important;
            border: 2px solid #000000 !important;
            color: #000000 !important;
        }
        /* White text inside notifications needs to be black */
        [data-testid="stNotification"] p, [data-testid="stNotification"] span {
            color: #000000 !important;
        }
        /* Metrics */
        .stMetric {
            background-color: white !important;
            border: 2px solid #000000 !important;
            padding: 15px !important;
            border-radius: 12px !important;
        }
        .stMetric [data-testid="stMetricValue"], .stMetric [data-testid="stMetricLabel"] {
            color: #000000 !important;
        }
        /* Tabs */
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(0, 0, 0, 0.2) !important;
            color: #ffffff !important;
            border-radius: 8px 8px 0 0 !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: #ffffff !important;
            color: #FF4B4B !important;
        }
        /* Mobile Layout */
        @media (max-width: 640px) {
            .stMain { padding: 0.5rem !important; }
            [data-testid="stDeckGlChart"] { height: 380px !important; }
            [data-testid="column"] {
                width: 100% !important;
                flex: none !important;
                margin-bottom: 15px;
            }
        }
        /* Card for the profile with black text on white background */
        .lead-card {
            background: white !important;
            padding: 1rem !important;
            border-radius: 10px !important;
            border: 2px solid #000000 !important;
            margin-bottom: 10px !important;
        }
        .lead-card div { color: #000000 !important; }
        </style>
    """, unsafe_allow_html=True)
# ... [Keeping Constants and init_db same] ...
# Constants
RAW_FILE = 'google.csv'
DB_FILE = 'leads_db.csv'
COLUMN_MAPPING = {
    'qBF1Pd': "Nombre del Local",
    'W4Efsd': "Categoría",
    'MW4etd': "Rating",
    'UY7F9': "Cantidad de Reseñas",
    'W4Efsd 4': "Dirección",
    'W4Efsd 6': "Horario",
    'ah5Ghc': "Reseña Destacada",
    'hfpxzc href': "URL",
    'A1zNzb href': "Website"
}

STATUS_OPTIONS = ["Por Contactar", "Contactado", "Visitado", "Demo", "Cliente"]
CHECKLIST_ITEMS = ["Verificar Teléfono", "Enviar Presentación", "Llamada Inicial", "Agendar Visita", "Visita Realizada"]
SYSTEM_OPTIONS = ["Sin Dato", "Fudo", "Bistrosoft", "BCN", "Otro"]
VENDOR_OPTIONS = ["Sin Asignar", "Seba", "Facu"]

def extract_coordinates(url):
    """Extracts latitude and longitude from Google Maps URL."""
    if not isinstance(url, str):
        return None, None
    match = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', url)
    if match:
        try:
            return float(match.group(1)), float(match.group(2))
        except ValueError:
            return None, None
    return None, None

def init_db():
    # ... Same as before ...
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
    elif os.path.exists(RAW_FILE):
        try:
            df = pd.read_csv(RAW_FILE, encoding='latin-1') # Fallback encoding
            df.dropna(how='all', inplace=True)
            if 'qBF1Pd' in df.columns:
                df = df[df['qBF1Pd'].notna()]
            present_keys = [k for k in COLUMN_MAPPING.keys() if k in df.columns]
            df = df[present_keys].copy()
            df.rename(columns=COLUMN_MAPPING, inplace=True)
            if "URL" in df.columns:
                coords = df["URL"].apply(extract_coordinates)
                df["latitude"] = coords.apply(lambda x: x[0])
                df["longitude"] = coords.apply(lambda x: x[1])
        except Exception:
            return None
    else:
        return None

    # Maintenance: Ensure Columns Exist
    if "Status" not in df.columns:
        df["Status"] = "Por Contactar"
    if "Notas" not in df.columns:
        df["Notas"] = ""
    if "Checklist" not in df.columns:
        df["Checklist"] = "{}"
    if "Interaction_Log" not in df.columns:
        df["Interaction_Log"] = "[]"
    if "Priority" not in df.columns:
        df["Priority"] = 0
    if "Sistema" not in df.columns:
        df["Sistema"] = "Sin Dato"
    if "Asignado_A" not in df.columns:
        df["Asignado_A"] = "Sin Asignar"
    if "Rating" in df.columns:
        df["Rating"] = df["Rating"].astype(str).str.replace(',', '.', regex=False)
        df["Rating"] = pd.to_numeric(df["Rating"], errors='coerce').fillna(0)

    # Type/Fill fixes
    df["Status"] = df["Status"].fillna("Por Contactar").astype(str)
    df["Notas"] = df["Notas"].fillna("").astype(str)
    df["Checklist"] = df["Checklist"].fillna("{}").astype(str)
    df["Interaction_Log"] = df["Interaction_Log"].fillna("[]").astype(str)
    
    if not os.path.exists(DB_FILE):
        df.to_csv(DB_FILE, index=False)
        
    return df

def save_db(df):
    df.to_csv(DB_FILE, index=False)

def get_status_color(status):
    if status == "Cliente":
        return [0, 255, 128, 255] 
    elif status in ["Visitado", "Demo"]:
        return [0, 128, 255, 255] 
    elif status == "Contactado":
        return [255, 165, 0, 255] 
    else: 
        return [255, 80, 80, 255]

def main():
    st.set_page_config(page_title="Lead Gen CRM", page_icon="🚀", layout="wide")
    local_css()

    if 'selected_lead_idx' not in st.session_state:
        st.session_state.selected_lead_idx = None
    if 'search_coords' not in st.session_state:
        st.session_state.search_coords = None

    df = init_db()
    if df is None:
        st.error("No Data Sources Found.")
        return

    st.title("🚀 Gamified CRM - Modo Campo")

    # Helper for encoding fix
    def clean_encoding(text):
        if not isinstance(text, str): return text
        # Fix common G-Maps scraper encoding issues
        clean = text.replace('', '').replace('â', '').replace('Â', '').replace('?', ' ')
        return clean.strip()

    tab_zone, tab_manage = st.tabs(["📍 Zona de Trabajo", "📝 Gestión de Tablero"])

    with tab_zone:
        col_search, col_status = st.columns([2, 2])
        with col_search:
            zone_query = st.text_input("🏢 ¿En qué zona trabajarás hoy?", placeholder="Ej. Vicente Lopez, Palermo...")
            if zone_query:
                # Geocode
                geolocator = Nominatim(user_agent="crm_agent")
                try:
                    # Append city/country for better context
                    loc = geolocator.geocode(f"{zone_query}, Buenos Aires, Argentina")
                    if loc:
                        st.session_state.search_coords = (loc.latitude, loc.longitude)
                        st.success(f"📍 Zona detectada: {loc.address}")
                    else:
                        st.session_state.search_coords = None
                        st.warning("⚠️ Zona no encontrada, usando búsqueda textual.")
                except Exception:
                    st.session_state.search_coords = None
                    
        with col_status:
            sel_status = st.multiselect("Filtro Rápido de Estado", options=STATUS_OPTIONS, default=[])

        # Filter Logic
        df_view = df.copy()
        
        # 1. Geo Filter (Radius 2km)
        if st.session_state.search_coords and "latitude" in df_view.columns:
            center = st.session_state.search_coords
            
            def is_within_radius(row):
                if pd.isna(row['latitude']) or pd.isna(row['longitude']):
                    return False
                try:
                    point = (row['latitude'], row['longitude'])
                    return geodesic(center, point).km <= 2.0 # 2km Radius
                except:
                    return False
            
            df_view = df_view[df_view.apply(is_within_radius, axis=1)]
            
        elif zone_query:
            # Fallback to Text Search
            df_view = df_view[
                df_view["Dirección"].str.contains(zone_query, case=False, na=False) | 
                df_view["Nombre del Local"].str.contains(zone_query, case=False, na=False) |
                df_view["URL"].str.contains(zone_query, case=False, na=False)
            ]
        
        if sel_status:
            df_view = df_view[df_view["Status"].isin(sel_status)]

        # Map / Profile Split
        idx = st.session_state.selected_lead_idx
        
        if idx is not None and idx in df.index:
            col_map, col_profile = st.columns([1, 1]) # 1:1 for better mobile stacking
        else:
            col_map = st.container()
            col_profile = None

        # ON MOBILE: If selected, show profile FIRST
        if idx is not None and idx in df.index:
             # This is a bit of a hack to ensure profile is seen first on mobile
             # But on Desktop it will be side by side
             pass

        # 1. MAP SECTION (Always Top)
        st.subheader(f"🗺️ Mapa ({len(df_view)} Locales)")
        if "latitude" in df_view.columns and not df_view.empty:
            map_data = df_view.dropna(subset=["latitude", "longitude"]).copy()
            if not map_data.empty:
                map_data["color"] = map_data["Status"].apply(get_status_color)
                map_data['orig_index'] = map_data.index 
                
                # Highlight Radius if searching
                layers = [pdk.Layer(
                    "ScatterplotLayer",
                    map_data,
                    get_position='[longitude, latitude]',
                    get_color='color',
                    get_radius=150,
                    pickable=True,
                    auto_highlight=True,
                    id="leads_layer"
                )]

                # View State logic
                if idx is not None and idx in map_data.index:
                    lat, lon, zoom = map_data.at[idx, "latitude"], map_data.at[idx, "longitude"], 15
                elif st.session_state.search_coords:
                    lat, lon, zoom = st.session_state.search_coords[0], st.session_state.search_coords[1], 13
                else:
                    lat, lon, zoom = map_data["latitude"].mean(), map_data["longitude"].mean(), 12

                event = st.pydeck_chart(pdk.Deck(
                    layers=layers,
                    initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=zoom, pitch=40),
                    tooltip={"html": "<b>{Nombre del Local}</b><br/>{Status}"},
                    map_style=None
                ), on_select="rerun", selection_mode="single-object", use_container_width=True)
                
                if event.selection:
                    objects_dict = event.selection.get("objects")
                    if objects_dict:
                        leads_objects = objects_dict.get("leads_layer", [])
                        if leads_objects:
                            selected_idx = leads_objects[0].get("orig_index")
                            if selected_idx is not None and selected_idx != st.session_state.selected_lead_idx:
                                st.session_state.selected_lead_idx = selected_idx
                                st.rerun()

        # 2. PROFILE SECTION (Appears here if selected, directly below map)
        if idx is not None and idx in df.index:
            row = df.loc[idx]
            st.markdown("---")
            
            # Mobile Close Button (Top)
            if st.button("⬅️ Ver Mapa completo", use_container_width=True, key="close_top"):
                st.session_state.selected_lead_idx = None
                st.rerun()

            st.markdown(f"""
            <div class="lead-card">
                <div style="margin:0; font-size: 1.4rem; font-weight: bold; color: #1f2937;">{row['Nombre del Local']}</div>
                <div style="color: #6b7280; font-size: 0.9rem; margin-top: 2px;">{row.get('Categoría','Comercio')}</div>
            </div>
            """, unsafe_allow_html=True)

            if row.get("URL"):
                st.link_button("🗺️ CÓMO LLEGAR (Google Maps)", row["URL"], type="primary", use_container_width=True)
            
            # Helper for display
            def clean_display_text(val, default="No especificado"):
                if pd.isna(val) or str(val).lower() == "nan" or str(val).strip() == "":
                    return default
                return val

            # Details Box
            addr = clean_encoding(clean_display_text(row.get('Dirección'), "Dirección no disponible"))
            rating = row.get('Rating', 0)
            hours = clean_encoding(clean_display_text(row.get('Horario'), "Horario no disponible"))
            web = clean_encoding(row.get("Website", "")) # Apply encoding fix here

            st.markdown(f"""
            <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border: 2px solid #000000; color: #000000; margin: 10px 0;">
                <p style="margin: 5px 0;">📍 <b>Dirección:</b> {addr}</p>
                <p style="margin: 5px 0;">⭐ <b>Rating:</b> {rating}</p>
                <p style="margin: 5px 0;">🕒 <b>Horario:</b> {hours}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if web and str(web) != "nan":
                 st.link_button("🌐 VER WEB / PEDIDO", web, use_container_width=True)

            # Status & Management
            c1, c2 = st.columns(2)
            curr_status = row["Status"]
            new_st = c1.selectbox("Estado", STATUS_OPTIONS, index=STATUS_OPTIONS.index(curr_status) if curr_status in STATUS_OPTIONS else 0, key=f"st_{idx}")
            
            curr_sys = row.get("Sistema", "Sin Dato")
            new_sys = c2.selectbox("Sistema", SYSTEM_OPTIONS, index=SYSTEM_OPTIONS.index(curr_sys) if curr_sys in SYSTEM_OPTIONS else 0, key=f"sys_{idx}")
            
            if new_st != curr_status or new_sys != curr_sys:
                 df.at[idx, "Status"] = new_st
                 df.at[idx, "Sistema"] = new_sys
                 save_db(df)
                 st.rerun()

            # Checklist
            with st.expander("✅ Checklist de Visita", expanded=False):
                checklist_data = json.loads(row.get("Checklist", "{}"))
                updated_cl = {}
                changed = False
                for item in CHECKLIST_ITEMS:
                    val = st.checkbox(item, value=checklist_data.get(item, False), key=f"chk_{idx}_{item}")
                    updated_cl[item] = val
                    if val != checklist_data.get(item, False):
                        changed = True
                if changed:
                    df.at[idx, "Checklist"] = json.dumps(updated_cl)
                    save_db(df)

            # Logs/Notes
            with st.expander("💬 Notas / Bitácora", expanded=False):
                logs = json.loads(row.get("Interaction_Log", "[]"))
                txt = st.text_input("Agregar nota...", key=f"note_{idx}")
                if st.button("Guardar Nota", key=f"btn_{idx}") and txt:
                    logs.insert(0, {"user": "Yo", "date": datetime.now().strftime("%H:%M"), "note": txt})
                    df.at[idx, "Interaction_Log"] = json.dumps(logs)
                    save_db(df)
                    st.rerun()
                for l in logs[:3]:
                    st.caption(f"{l['date']} - {l['note']}")

        # 3. LIST & METRICS (Bottom)
        st.divider()
        st.caption("👇 Lista de Locales:")
        event_list = st.dataframe(
            df_view[["Nombre del Local", "Status", "Dirección"]],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        if event_list.selection and event_list.selection.rows:
            row_idx = event_list.selection.rows[0]
            real_idx = df_view.index[row_idx]
            if real_idx != st.session_state.selected_lead_idx:
                 st.session_state.selected_lead_idx = real_idx
                 st.rerun()

        st.markdown("---")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Zona", len(df_view))
        m2.metric("Clientes", len(df_view[df_view["Status"]=="Cliente"]))
        m3.metric("Pendientes", len(df_view[df_view["Status"]=="Por Contactar"]))

    # --- TAB 2: GESTIÓN DE TABLERO ---
    with tab_manage:
        st.subheader("📋 Base de Datos de Leads")
        
        # Add Lead Form
        with st.expander("➕ Agregar Nuevo Lead Manualmente"):
            with st.form("add_lead"):
                c1, c2 = st.columns(2)
                new_name = c1.text_input("Nombre del Local")
                new_address = c2.text_input("Dirección")
                new_cat = c1.text_input("Categoría", value="Hamburguesa")
                new_lat = c2.number_input("Latitud (Opcional)", value=0.0, format="%.6f")
                new_lon = c1.number_input("Longitud (Opcional)", value=0.0, format="%.6f")
                
                if st.form_submit_button("Crear Lead"):
                    if new_name:
                        new_row = {
                            "Nombre del Local": new_name,
                            "Dirección": new_address,
                            "Categoría": new_cat,
                            "Status": "Por Contactar",
                            "latitude": new_lat if new_lat != 0 else None,
                            "longitude": new_lon if new_lon != 0 else None,
                            "Checklist": "{}",
                            "Interaction_Log": "[]",
                            "Rating": 0
                        }
                        # Append using pandas concat
                        new_df_row = pd.DataFrame([new_row])
                        df = pd.concat([df, new_df_row], ignore_index=True)
                        save_db(df)
                        st.success(f"Lead '{new_name}' creado!")
                        st.rerun()
                    else:
                        st.error("El nombre es obligatorio")
        
        # Full Editor
        edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic", key="full_editor")
        if not df.equals(edited_df):
            df.update(edited_df)
            save_db(df)

if __name__ == "__main__":
    main()
