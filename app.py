# ============================================================
#  BioCare Dashboard - Bioingenieros SAC / INCOR EsSalud
#  PASO 7: Los 4 modulos completos
# ============================================================

import dash
from dash import html, dcc, Input, Output
import pandas as pd
import calculos
import graficos
import alertas
import prediccion
import automatizacion

# --- 1. Cargar datos y calcular todo ---
equipos, historial = calculos.cargar_datos()
disponibilidad, operativos, total_eq = calculos.kpi_disponibilidad(equipos)
cumplimiento = calculos.kpi_cumplimiento(historial)
mtbf = calculos.kpi_mtbf(historial)
mttr = calculos.kpi_mttr(historial)
costo_total = calculos.kpi_costo(historial)

fig_cumplimiento = graficos.grafico_cumplimiento()
fig_estado = graficos.grafico_estado(equipos)
fig_mtbf = graficos.grafico_mtbf(equipos, historial)
fig_costo = graficos.grafico_costo(equipos, historial)

criticidad = calculos.calcular_criticidad(equipos, historial)
lista_alertas = alertas.generar_alertas(equipos, historial)
texto_correo = alertas.construir_correo(lista_alertas)
prediccion_df = prediccion.entrenar_y_predecir(equipos, historial)

# Modulo 5: entrenar clasificador y preparar datos de automatizacion
modelo_clf, clf_acc, clf_cv = automatizacion.entrenar_clasificador(historial)
lista_codigos = equipos["codigo"].tolist()

# ============================================================
#  SISTEMA DE USUARIOS Y ROLES (Etapa 2)
# ============================================================
# Cada usuario tiene: contrasena, nombre completo y rol.
# NOTA ACADEMICA: en un sistema real las contrasenas estarian
# encriptadas y en una base de datos segura. Para este proyecto
# academico se usan en texto simple con fines de demostracion.
USUARIOS = {
    "admin": {
        "password": "admin2026",
        "nombre": "Ing. Miguel Valdivia Morales",
        "rol": "Supervisor",
        "modulos": ["inicio","kpis","crit","alertas","pred","auto"],
    },
    "tecnico": {
        "password": "tecnico2026",
        "nombre": "Tecnico de Mantenimiento",
        "rol": "Tecnico",
        "modulos": ["inicio","kpis","crit","alertas","auto"],
    },
    "invitado": {
        "password": "biocare2026",
        "nombre": "Invitado (Jurado)",
        "rol": "Visualizacion",
        "modulos": ["inicio","kpis","crit","pred"],
    },
}

# Nombres de rol con color para mostrar
COLOR_ROL = {"Supervisor":"#1f9d6b","Tecnico":"#0d5c7d","Visualizacion":"#6c5ce0"}




COLOR_NIVEL = {"ALTO":"#d94862","MEDIO":"#dd9324","BAJO":"#1f9d6b"}
BG_NIVEL = {"ALTO":"#fdebef","MEDIO":"#fdf3e0","BAJO":"#e4f7ef"}
COLOR_ALERTA = {"CRITICA":"#d94862","ALTA":"#dd9324","MEDIA":"#6c5ce0"}
BG_ALERTA = {"CRITICA":"#fdebef","ALTA":"#fdf3e0","MEDIA":"#ece9fb"}

# Estilo para los botones de ejemplo rapido del clasificador (Automatizacion)
ESTILO_CHIP = {
    "backgroundColor":"rgba(255,255,255,0.18)", "color":"white", "border":"1px solid rgba(255,255,255,0.4)",
    "borderRadius":"20px", "padding":"5px 12px", "fontSize":"11px", "fontWeight":"600",
    "cursor":"pointer", "whiteSpace":"nowrap"
}

# --- 2. Componentes reutilizables ---
def tarjeta_kpi(icono, etiqueta, valor, unidad, meta, color):
    return html.Div(children=[
        html.Div(icono, style={"fontSize":"22px","marginBottom":"10px"}),
        html.Div(etiqueta, style={"fontSize":"12px","color":"#8499b1","fontWeight":"600",
                                  "textTransform":"uppercase","letterSpacing":"0.5px","minHeight":"32px"}),
        html.Div(children=[
            html.Span(valor, style={"fontSize":"32px","fontWeight":"700","color":color}),
            html.Span(" "+unidad, style={"fontSize":"15px","color":"#8499b1","fontWeight":"600"})
        ]),
        html.Div(meta, style={"fontSize":"11.5px","color":"#8499b1","marginTop":"6px"})
    ], className="tarjeta-hover", style={"backgroundColor":"white","padding":"22px","borderRadius":"14px",
              "boxShadow":"0 4px 16px rgba(8,55,77,0.08)","flex":"1","borderTop":"3px solid "+color})

def tarjeta_kpi_avanzada(icono, etiqueta, valor, unidad, estado_meta, color):
    """
    Tarjeta KPI con semaforo de cumplimiento de meta.
    estado_meta es una tupla (texto, color_semaforo, simbolo).
    """
    texto_meta, color_sem, simbolo = estado_meta
    return html.Div(children=[
        html.Div(children=[
            html.Span(icono, style={"fontSize":"22px"}),
            html.Span(simbolo, style={"fontSize":"15px","float":"right","color":color_sem})
        ], style={"marginBottom":"10px"}),
        html.Div(etiqueta, style={"fontSize":"12px","color":"#8499b1","fontWeight":"600",
                                  "textTransform":"uppercase","letterSpacing":"0.5px","minHeight":"32px"}),
        html.Div(children=[
            html.Span(valor, style={"fontSize":"32px","fontWeight":"700","color":color}),
            html.Span(" "+unidad, style={"fontSize":"15px","color":"#8499b1","fontWeight":"600"})
        ]),
        html.Div(children=[
            html.Span("●", style={"fontSize":"10px","color":color_sem,"marginRight":"5px"}),
            html.Span(texto_meta, style={"fontSize":"11.5px","color":"#3f5874","fontWeight":"600"})
        ], style={"marginTop":"6px"})
    ], className="tarjeta-hover", style={"backgroundColor":"white","padding":"22px","borderRadius":"14px",
              "boxShadow":"0 4px 16px rgba(8,55,77,0.08)","flex":"1","minWidth":"180px","borderTop":"3px solid "+color})

def evaluar_meta(valor, meta, mayor_mejor=True):
    """Devuelve (texto, color, simbolo) segun si el valor cumple la meta."""
    if mayor_mejor:
        if valor >= meta:
            return (f"Cumple meta (>= {meta})", "#1f9d6b", "▲")
        elif valor >= meta * 0.9:
            return (f"Cerca de meta ({meta})", "#dd9324", "▶")
        else:
            return (f"Bajo meta ({meta})", "#d94862", "▼")
    else:
        if valor <= meta:
            return (f"Cumple meta (<= {meta})", "#1f9d6b", "▲")
        elif valor <= meta * 1.1:
            return (f"Cerca de meta ({meta})", "#dd9324", "▶")
        else:
            return (f"Sobre meta ({meta})", "#d94862", "▼")

def tarjeta_grafico(titulo, figura):
    return html.Div(children=[
        html.Div(titulo, style={"fontSize":"14px","fontWeight":"700","color":"#08374d",
                                "padding":"16px 20px","borderBottom":"1px solid #e0e7f0"}),
        html.Div(dcc.Graph(figure=figura, config={"displayModeBar":False}), style={"padding":"12px"})
    ], style={"backgroundColor":"white","borderRadius":"14px",
              "boxShadow":"0 4px 16px rgba(8,55,77,0.08)","flex":"1","overflow":"hidden"})

def tarjeta_resumen(nivel, cantidad, descripcion, colores, bgs):
    return html.Div(children=[
        html.Div(str(cantidad), style={"fontSize":"40px","fontWeight":"700","color":colores[nivel]}),
        html.Div(descripcion, style={"fontSize":"12px","color":"#3f5874","marginTop":"2px"})
    ], className="tarjeta-hover", style={"backgroundColor":"white","padding":"20px 22px","borderRadius":"14px",
              "boxShadow":"0 4px 16px rgba(8,55,77,0.08)","flex":"1",
              "borderLeft":"5px solid "+colores[nivel]})

# --- 3. MODULO 1 ---
def contenido_modulo1():
    anios = calculos.anios_disponibles(historial)
    return html.Div(children=[
        html.H2("Indicadores Clave de Desempeno", style={"color":"#08374d","fontWeight":"700","marginBottom":"4px"}),
        html.P("Cinco KPIs y cuatro visualizaciones sobre el historial de mantenimiento de los 30 equipos.",
               style={"color":"#3f5874","fontSize":"14px","marginBottom":"18px"}),

        # Filtro temporal por anio
        html.Div(children=[
            html.Span("Periodo de analisis:", style={"fontSize":"12.5px","fontWeight":"600","color":"#3f5874","marginRight":"12px"}),
            dcc.Dropdown(id="filtro-anio-kpi",
                options=[{"label":"Todo el historial (2022-2026)","value":"todos"}] +
                        [{"label":f"Ano {a}","value":a} for a in anios],
                value="todos", clearable=False,
                style={"fontSize":"13px","width":"280px"})
        ], style={"display":"flex","alignItems":"center","marginBottom":"20px","backgroundColor":"white",
                  "padding":"14px 18px","borderRadius":"12px","boxShadow":"0 4px 16px rgba(8,55,77,0.06)"}),

        # Tarjetas KPI (se actualizan con el filtro)
        html.Div(id="contenedor-kpis", children=construir_tarjetas_kpi("todos"),
                 style={"display":"flex","gap":"14px","marginBottom":"22px","flexWrap":"wrap"}),

        # Graficos (se actualizan con el filtro de anio)
        html.Div(id="contenedor-graficos-kpi", children=construir_graficos_kpi("todos"))
    ])

def construir_graficos_kpi(anio):
    """Construye los graficos del modulo KPIs segun el anio."""
    fig_cump = graficos.grafico_cumplimiento(historial, anio)
    fig_est = graficos.grafico_estado(equipos)
    fig_mt = graficos.grafico_mtbf(equipos, historial, anio)
    fig_co = graficos.grafico_costo(equipos, historial, anio)
    fig_evol = graficos.grafico_evolucion(historial, anio)
    fig_dist = graficos.grafico_distribucion(historial, anio)
    titulo_cump = "Cumplimiento del Mantenimiento Preventivo (2025 vs 2026)" if anio == "todos" else f"Cumplimiento Preventivo Mensual ({anio})"
    titulo_evol = "Evolucion de Mantenimientos por Ano" if anio == "todos" else f"Evolucion Mensual de Mantenimientos ({anio})"
    return html.Div(children=[
        html.Div(children=[
            tarjeta_grafico(titulo_cump, fig_cump),
            tarjeta_grafico("Estado del Parque Tecnologico", fig_est),
        ], style={"display":"flex","gap":"16px","marginBottom":"16px"}),
        html.Div(children=[
            tarjeta_grafico("MTBF por Tipo de Equipo", fig_mt),
            tarjeta_grafico("Costo Acumulado por Tipo de Equipo", fig_co),
        ], style={"display":"flex","gap":"16px","marginBottom":"16px"}),
        # Nuevos graficos: evolucion temporal y distribucion
        html.Div(children=[
            tarjeta_grafico(titulo_evol, fig_evol),
            tarjeta_grafico("Distribucion Preventivos vs Correctivos", fig_dist),
        ], style={"display":"flex","gap":"16px","marginBottom":"16px"}),
        # Rankings de equipos criticos
        html.Div(children=[
            tarjeta_ranking("Top 5 equipos por costo", calculos.ranking_equipos(equipos, historial, "costo", anio, 5), "costo"),
            tarjeta_ranking("Top 5 equipos por fallas", calculos.ranking_equipos(equipos, historial, "fallas", anio, 5), "fallas"),
        ], style={"display":"flex","gap":"16px","marginBottom":"16px"}),
        # Analisis por area clinica
        html.Div(children=[
            tarjeta_grafico("Fallas Correctivas por Area Clinica", graficos.grafico_area(equipos, historial, anio)),
        ]),
    ])

def tarjeta_ranking(titulo, datos, tipo):
    """Construye una tarjeta con un ranking de equipos."""
    filas = []
    colores_pos = ["#d94862","#dd9324","#6c5ce0","#0d5c7d","#8499b1"]
    for i, (cod, nombre, valor) in enumerate(datos):
        valor_txt = f"S/ {valor:,.0f}" if tipo == "costo" else f"{valor} fallas"
        filas.append(html.Div(children=[
            html.Div(children=[
                html.Span(f"{i+1}", style={"backgroundColor":colores_pos[i],"color":"white","borderRadius":"50%",
                          "width":"22px","height":"22px","display":"inline-flex","alignItems":"center",
                          "justifyContent":"center","fontSize":"11px","fontWeight":"700","marginRight":"10px"}),
                html.Span(cod, style={"fontSize":"11px","color":"#8499b1","fontFamily":"monospace","marginRight":"8px"}),
                html.Span(nombre[:26], style={"fontSize":"12px","color":"#0b2238","fontWeight":"600"})
            ], style={"display":"flex","alignItems":"center","flex":"1"}),
            html.Span(valor_txt, style={"fontSize":"12px","fontWeight":"700","color":colores_pos[i],"fontFamily":"monospace"})
        ], style={"display":"flex","justifyContent":"space-between","alignItems":"center",
                  "padding":"10px 12px","borderBottom":"1px solid #eef2f7"}))
    return html.Div(children=[
        html.Div(titulo, style={"fontSize":"14px","fontWeight":"700","color":"#08374d",
                 "padding":"16px 18px","borderBottom":"1px solid #e0e7f0"}),
        html.Div(filas, style={"padding":"6px 8px"})
    ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","flex":"1"})

def construir_tarjetas_kpi(anio):
    """Construye las tarjetas KPI segun el anio seleccionado, con tendencia comparativa."""
    # Disponibilidad no depende del anio (es estado actual)
    disp, oper, tot = calculos.kpi_disponibilidad(equipos)
    # Los demas KPIs si dependen del periodo
    k = calculos.kpis_por_anio(historial, anio)
    costo_prom = calculos.kpi_costo_promedio(historial, anio)
    sufijo = "" if anio == "todos" else f" ({anio})"

    # Calcular tendencias (comparacion con el anio anterior)
    t_mtbf = calculos.calcular_tendencia(historial, anio, "mtbf")
    t_mttr = calculos.calcular_tendencia(historial, anio, "mttr")
    t_costo = calculos.calcular_tendencia(historial, anio, "costo")

    return [
        tarjeta_kpi_avanzada("🟢","Tasa de Disponibilidad", f"{disp:.1f}","%",
                             evaluar_meta(disp, 85, True), "#1f9d6b"),
        tarjeta_kpi_avanzada("🗓️","Cumpl. Preventivo", f"{k['cumplimiento']:.1f}","%",
                             evaluar_meta(k['cumplimiento'], 85, True), "#0d5c7d"),
        tarjeta_kpi_avanzada("⏱️","MTBF entre fallas", f"{k['mtbf']:.0f}","dias",
                             tendencia_meta(t_mtbf, "dias", True), "#6c5ce0"),
        tarjeta_kpi_avanzada("🔧","MTTR reparacion", f"{k['mttr']:.1f}","hrs",
                             tendencia_meta(t_mttr, "hrs", False), "#dd9324"),
        tarjeta_kpi_avanzada("💰","Costo Total", f"S/ {k['costo']/1000:.0f}","k",
                             tendencia_meta(t_costo, "costo", False) if t_costo is not None else ("Total"+sufijo, "#8499b1", "■"), "#13b0a5"),
        tarjeta_kpi_avanzada("📊","Costo x Intervencion", f"S/ {costo_prom:.0f}","",
                             ("Promedio correctivo"+sufijo, "#8499b1", "■"), "#d94862"),
    ]

def tendencia_meta(cambio, tipo, mayor_mejor):
    """Devuelve (texto, color, simbolo) para mostrar la tendencia vs anio anterior."""
    if cambio is None:
        return ("Sin comparacion previa", "#8499b1", "■")
    # Determinar si el cambio es bueno o malo
    if mayor_mejor:
        es_bueno = cambio > 0
    else:
        es_bueno = cambio < 0
    color = "#1f9d6b" if es_bueno else "#d94862"
    simbolo = "▲" if cambio > 0 else ("▼" if cambio < 0 else "■")
    return (f"{cambio:+.1f}% vs ano anterior", color, simbolo)

# --- 4. MODULO 2 ---
def fila_tabla(r):
    return html.Tr(children=[
        html.Td(r["cod"], style={"padding":"10px 12px","fontSize":"11px","color":"#8499b1","fontFamily":"monospace"}),
        html.Td(r["nombre"], style={"padding":"10px 12px","fontWeight":"600","color":"#0b2238","fontSize":"12.5px"}),
        html.Td(r["area"], style={"padding":"10px 12px","fontSize":"11.5px","color":"#8499b1"}),
        html.Td(str(r["indice"]), style={"padding":"10px 12px","fontWeight":"700",
                "color":COLOR_NIVEL[r["nivel"]],"fontFamily":"monospace","fontSize":"14px"}),
        html.Td(html.Span(r["nivel"].capitalize(), style={
            "backgroundColor":BG_NIVEL[r["nivel"]],"color":COLOR_NIVEL[r["nivel"]],
            "padding":"3px 11px","borderRadius":"30px","fontSize":"11px","fontWeight":"600"}),
            style={"padding":"10px 12px"})
    ], id={"tipo":"fila-equipo","codigo":r["cod"]}, className="fila-tabla",
       n_clicks=0, style={"borderBottom":"1px solid #e0e7f0","cursor":"pointer"})

def celda_heatmap(r):
    return html.Div(children=[
        html.Div(str(r["indice"]), style={"fontSize":"18px","fontWeight":"700","fontFamily":"monospace"}),
        html.Div(r["cod"], style={"fontSize":"9px","opacity":"0.7"})
    ], style={"backgroundColor":BG_NIVEL[r["nivel"]],"color":COLOR_NIVEL[r["nivel"]],
              "borderRadius":"12px","padding":"14px 8px","textAlign":"center"})

def contenido_modulo2():
    n_alto = (criticidad["nivel"]=="ALTO").sum()
    n_medio = (criticidad["nivel"]=="MEDIO").sum()
    n_bajo = (criticidad["nivel"]=="BAJO").sum()
    areas = sorted(criticidad["area"].unique())
    return html.Div(children=[
        html.H2("Matriz de Criticidad Clinica", style={"color":"#08374d","fontWeight":"700","marginBottom":"4px"}),
        html.P("Clasificacion automatica de los 30 equipos segun su indice de criticidad compuesto.",
               style={"color":"#3f5874","fontSize":"14px","marginBottom":"20px"}),

        # Barra de filtros globales
        html.Div(children=[
            html.Div(children=[
                html.Span("Filtrar por area:", style={"fontSize":"12px","fontWeight":"600","color":"#3f5874","marginBottom":"6px","display":"block"}),
                dcc.Dropdown(id="filtro-area",
                    options=[{"label":"Todas las areas","value":"todas"}] + [{"label":a,"value":a} for a in areas],
                    value="todas", clearable=False, style={"fontSize":"13px"})
            ], style={"flex":"1"}),
            html.Div(children=[
                html.Span("Filtrar por criticidad:", style={"fontSize":"12px","fontWeight":"600","color":"#3f5874","marginBottom":"6px","display":"block"}),
                dcc.Dropdown(id="filtro-nivel",
                    options=[{"label":"Todos los niveles","value":"todos"},
                             {"label":"Alto","value":"ALTO"},
                             {"label":"Medio","value":"MEDIO"},
                             {"label":"Bajo","value":"BAJO"}],
                    value="todos", clearable=False, style={"fontSize":"13px"})
            ], style={"flex":"1"}),
        ], style={"display":"flex","gap":"14px","marginBottom":"20px","backgroundColor":"white",
                  "padding":"16px 18px","borderRadius":"12px","boxShadow":"0 4px 16px rgba(8,55,77,0.06)"}),

        # Botones de descarga de reportes
        html.Div(children=[
            html.Span("Exportar reporte:", style={"fontSize":"12.5px","fontWeight":"600","color":"#3f5874","marginRight":"4px"}),
            html.Button("📊  Descargar Excel", id="btn-excel", n_clicks=0, className="boton-hover",
                        style={"backgroundColor":"#1f9d6b","color":"white","border":"none","borderRadius":"9px",
                               "padding":"10px 18px","fontSize":"12.5px","fontWeight":"700","cursor":"pointer"}),
            html.Button("📄  Descargar PDF", id="btn-pdf", n_clicks=0, className="boton-hover",
                        style={"backgroundColor":"#d94862","color":"white","border":"none","borderRadius":"9px",
                               "padding":"10px 18px","fontSize":"12.5px","fontWeight":"700","cursor":"pointer"}),
            # Componente invisible que realiza la descarga
            dcc.Download(id="descarga-reporte")
        ], style={"display":"flex","gap":"10px","alignItems":"center","marginBottom":"20px"}),

        html.Div(id="tarjetas-resumen-crit", children=[
            tarjeta_resumen("ALTO", n_alto, "Criticidad Alta (indice >= 70)", COLOR_NIVEL, BG_NIVEL),
            tarjeta_resumen("MEDIO", n_medio, "Criticidad Media (40-69)", COLOR_NIVEL, BG_NIVEL),
            tarjeta_resumen("BAJO", n_bajo, "Criticidad Baja (< 40)", COLOR_NIVEL, BG_NIVEL),
        ], style={"display":"flex","gap":"14px","marginBottom":"22px"}),
        html.Div(children=[
            html.Div(children=[
                html.Div("Registro de equipos por criticidad", style={"fontSize":"14px","fontWeight":"700",
                         "color":"#08374d","padding":"16px 20px","borderBottom":"1px solid #e0e7f0"}),
                # Buscador en tiempo real
                html.Div(children=[
                    dcc.Input(id="buscador-equipos", type="text",
                              placeholder="🔍  Buscar por codigo, nombre o area...",
                              className="login-input",
                              style={"width":"100%","height":"42px","padding":"0 14px","borderRadius":"10px",
                                     "border":"1.5px solid #e0e7f0","fontSize":"13px","boxSizing":"border-box",
                                     "color":"#08374d"})
                ], style={"padding":"14px 16px 4px"}),
                html.Div(html.Table(children=[
                    html.Thead(html.Tr(children=[
                        html.Th(h, style={"backgroundColor":"#08374d","color":"white","padding":"11px 12px",
                                "textAlign":"left","fontSize":"10.5px","textTransform":"uppercase"})
                        for h in ["Codigo","Equipo","Area","Indice","Nivel"]])),
                    html.Tbody(id="cuerpo-tabla-crit", children=[fila_tabla(r) for _, r in criticidad.iterrows()])
                ], style={"width":"100%","borderCollapse":"collapse"}), style={"padding":"0 8px"})
            ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)",
                      "flex":"1.6","overflow":"hidden"}),
            html.Div(children=[
                html.Div("Mapa de calor", style={"fontSize":"14px","fontWeight":"700","color":"#08374d",
                         "padding":"16px 20px","borderBottom":"1px solid #e0e7f0"}),
                html.Div(id="heatmap-crit", children=[celda_heatmap(r) for _, r in criticidad.iterrows()],
                         style={"display":"grid","gridTemplateColumns":"repeat(4, 1fr)","gap":"9px","padding":"18px"})
            ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)",
                      "flex":"1","overflow":"hidden"})
        ], style={"display":"flex","gap":"16px","alignItems":"flex-start"})
    ])

# --- Ficha detallada del equipo (ventana modal) ---
def calcular_salud_equipo(r, h, estado):
    """Calcula un indicador de salud del equipo (0-100) combinando varios factores."""
    salud = 100
    # Penalizar por estado operativo
    if estado == "Inoperativo":
        salud -= 45
    elif estado == "En reparacion":
        salud -= 25
    # Penalizar por criticidad alta
    if r["nivel"] == "ALTO":
        salud -= 15
    elif r["nivel"] == "MEDIO":
        salud -= 7
    # Penalizar por fallas correctivas recientes (ultimos 90 dias)
    corr = h[h["tipo_mantenimiento"]=="Correctivo"]
    FECHA_HOY = pd.Timestamp("2026-05-31")
    recientes = corr[corr["fecha"] > (FECHA_HOY - pd.Timedelta(days=90))]
    salud -= min(25, len(recientes) * 5)
    # Penalizar por antiguedad cercana a vida util
    if r["antiguedad"] >= 9:
        salud -= 10
    elif r["antiguedad"] >= 7:
        salud -= 5
    salud = max(5, min(100, salud))
    # Etiqueta y color segun el nivel de salud
    if salud >= 75:
        return salud, "Buena", "#1f9d6b"
    elif salud >= 50:
        return salud, "Regular", "#dd9324"
    else:
        return salud, "Critica", "#d94862"

def barra_acciones_ficha(codigo, rol):
    """Construye la barra de botones de accion segun el rol del usuario."""
    # Definir que acciones puede hacer cada rol
    puede_registrar = rol in ["Supervisor", "Tecnico"]
    puede_descargar_hist = rol in ["Supervisor", "Tecnico"]
    puede_cambiar_estado = rol in ["Supervisor", "Tecnico"]
    puede_programar = rol == "Supervisor"
    # Exportar ficha: todos los roles

    botones = []
    # Exportar ficha tecnica (todos)
    botones.append(html.Button("📄  Exportar ficha", id={"tipo":"accion-ficha","accion":"exportar","cod":codigo},
                   n_clicks=0, className="boton-hover", style=estilo_boton_accion("#0d5c7d")))
    if puede_registrar:
        botones.append(html.Button("➕  Registrar OTM", id={"tipo":"accion-ficha","accion":"registrar","cod":codigo},
                       n_clicks=0, className="boton-hover", style=estilo_boton_accion("#1f9d6b")))
    if puede_descargar_hist:
        botones.append(html.Button("⬇  Descargar historial", id={"tipo":"accion-ficha","accion":"descargar","cod":codigo},
                       n_clicks=0, className="boton-hover", style=estilo_boton_accion("#6c5ce0")))
    if puede_cambiar_estado:
        botones.append(html.Button("🔧  Cambiar estado", id={"tipo":"accion-ficha","accion":"estado","cod":codigo},
                       n_clicks=0, className="boton-hover", style=estilo_boton_accion("#dd9324")))
    if puede_programar:
        botones.append(html.Button("📅  Programar mant.", id={"tipo":"accion-ficha","accion":"programar","cod":codigo},
                       n_clicks=0, className="boton-hover", style=estilo_boton_accion("#13b0a5")))

    return html.Div(children=[
        html.Div("Acciones disponibles", style={"fontSize":"10px","color":"#8499b1","fontWeight":"600",
                 "textTransform":"uppercase","letterSpacing":"0.5px","marginBottom":"8px"}),
        html.Div(botones, style={"display":"flex","gap":"8px","flexWrap":"wrap"})
    ], style={"backgroundColor":"#f7fafc","border":"1px dashed #cfd9e6","borderRadius":"10px",
              "padding":"14px 16px","marginBottom":"18px"})

def estilo_boton_accion(color):
    return {"backgroundColor":color,"color":"white","border":"none","borderRadius":"8px",
            "padding":"9px 14px","fontSize":"11.5px","fontWeight":"700","cursor":"pointer"}

def formulario_registrar_otm(codigo):
    """Formulario modal para registrar una nueva OTM en un equipo."""
    nombre = equipos[equipos["codigo"]==codigo]["nombre"].values[0]
    estilo_input = {"width":"100%","height":"42px","padding":"0 13px","borderRadius":"9px",
                    "border":"1.5px solid #e0e7f0","fontSize":"13px","boxSizing":"border-box","color":"#08374d"}
    estilo_label = {"fontSize":"11.5px","fontWeight":"600","color":"#3f5874","marginBottom":"5px","display":"block","marginTop":"12px"}
    return html.Div(children=[
        html.Div(id={"tipo":"cerrar-form","origen":"fondo"}, n_clicks=0, style={
            "position":"fixed","top":"0","left":"0","width":"100%","height":"100%",
            "backgroundColor":"rgba(8,55,77,0.6)","zIndex":"1100"}),
        html.Div(children=[
            # Cabecera
            html.Div(children=[
                html.Div(children=[
                    html.Div("REGISTRAR ORDEN DE TRABAJO", style={"fontSize":"11px","fontWeight":"700","color":"rgba(255,255,255,0.85)","letterSpacing":"1.2px"}),
                    html.Div(f"{codigo} - {nombre}", style={"fontSize":"15px","fontWeight":"700","color":"white","marginTop":"2px"})
                ]),
                html.Button("X", id={"tipo":"cerrar-form","origen":"boton"}, n_clicks=0, style={
                    "backgroundColor":"rgba(255,255,255,0.2)","color":"white","border":"none",
                    "borderRadius":"8px","width":"30px","height":"30px","fontSize":"14px","fontWeight":"700","cursor":"pointer"})
            ], style={"display":"flex","justifyContent":"space-between","alignItems":"center",
                      "background":"linear-gradient(120deg, #08374d, #1f9d6b)","padding":"18px 24px"}),
            # Cuerpo del formulario
            html.Div(children=[
                # Tipo de mantenimiento
                html.Label("Tipo de mantenimiento", style=estilo_label),
                dcc.Dropdown(id="otm-tipo",
                    options=[{"label":"Correctivo","value":"Correctivo"},{"label":"Preventivo","value":"Preventivo"}],
                    value="Correctivo", clearable=False, style={"fontSize":"13px"}, maxHeight=160),
                # Descripcion + clasificador
                html.Label("Descripcion de la falla o trabajo", style=estilo_label),
                html.Div(children=[
                    dcc.Input(id="otm-descripcion", type="text", placeholder="Ej.: el monitor no enciende",
                              style={**estilo_input,"flex":"1"}),
                    html.Button("🤖 Clasificar", id="otm-btn-clasificar", n_clicks=0, className="boton-hover",
                                style={"backgroundColor":"#13b0a5","color":"white","border":"none","borderRadius":"9px",
                                       "padding":"0 16px","height":"42px","fontSize":"12px","fontWeight":"700","cursor":"pointer","marginLeft":"8px","whiteSpace":"nowrap"})
                ], style={"display":"flex"}),
                # Categoria (la sugiere el clasificador)
                html.Label("Categoria de falla (sugerida automaticamente)", style=estilo_label),
                dcc.Dropdown(id="otm-categoria",
                    options=[{"label":c,"value":c} for c in ["Eléctrica","Mecánica","Sensores","Software","Calibración","Desgaste"]],
                    placeholder="Se completara al clasificar, o eligela manualmente", style={"fontSize":"13px"}),
                html.Div(id="otm-clasificacion-info", style={"fontSize":"11.5px","color":"#13b0a5","marginTop":"6px","fontWeight":"600"}),
                # Fila de tres columnas: urgencia, tecnico, estado final
                html.Div(children=[
                    html.Div(children=[
                        html.Label("Urgencia", style=estilo_label),
                        dcc.Dropdown(id="otm-urgencia",
                            options=[{"label":u,"value":u} for u in ["Alta","Media","Baja"]],
                            value="Media", clearable=False, style={"fontSize":"13px"}, maxHeight=140)
                    ], style={"flex":"1","marginRight":"10px"}),
                    html.Div(children=[
                        html.Label("Tecnico responsable", style=estilo_label),
                        dcc.Dropdown(id="otm-tecnico",
                            options=[{"label":t,"value":t} for t in ["J. Ramírez","M. Torres","L. Quispe","A. Flores"]],
                            value="J. Ramírez", clearable=False, style={"fontSize":"13px"}, maxHeight=140)
                    ], style={"flex":"1","marginRight":"10px"}),
                    html.Div(children=[
                        html.Label("Estado final", style=estilo_label),
                        dcc.Dropdown(id="otm-estado",
                            options=[{"label":e,"value":e} for e in ["Operativo","En observación"]],
                            value="Operativo", clearable=False, style={"fontSize":"13px"}, maxHeight=140)
                    ], style={"flex":"1"})
                ], style={"display":"flex"}),
                # Costo y horas (campos numericos, no se despliegan)
                html.Div(children=[
                    html.Div(children=[
                        html.Label("Costo (S/)", style=estilo_label),
                        dcc.Input(id="otm-costo", type="number", value=0, min=0, style=estilo_input)
                    ], style={"flex":"1","marginRight":"10px"}),
                    html.Div(children=[
                        html.Label("Duracion (horas)", style=estilo_label),
                        dcc.Input(id="otm-horas", type="number", value=1, min=0, style=estilo_input)
                    ], style={"flex":"1"})
                ], style={"display":"flex"}),
                # Guardar la referencia del equipo
                dcc.Store(id="otm-codigo-actual", data=codigo),
                # Boton guardar
                html.Button("Guardar orden de trabajo", id="otm-btn-guardar", n_clicks=0, className="boton-hover",
                            style={"width":"100%","height":"46px","backgroundColor":"#1f9d6b","color":"white",
                                   "border":"none","borderRadius":"10px","fontSize":"14px","fontWeight":"700",
                                   "cursor":"pointer","marginTop":"20px"}),
                html.Div(id="otm-mensaje-guardado", style={"fontSize":"12.5px","textAlign":"center","marginTop":"10px","fontWeight":"600"}),
                # Espaciador para que los desplegables tengan espacio al abrirse
                html.Div(style={"height":"160px"})
            ], style={"padding":"20px 24px 24px","maxHeight":"70vh","overflowY":"auto","overflowX":"visible"})
        ], style={"position":"fixed","top":"50%","left":"50%","transform":"translate(-50%, -50%)",
                  "backgroundColor":"white","borderRadius":"16px","width":"540px","maxWidth":"94%",
                  "zIndex":"1101","boxShadow":"0 30px 80px rgba(8,55,77,0.45)","overflow":"hidden"})
    ])

def formulario_cambiar_estado(codigo):
    """Formulario modal para cambiar el estado operativo de un equipo."""
    nombre = equipos[equipos["codigo"]==codigo]["nombre"].values[0]
    eq_estado = calculos.estado_equipos(equipos)
    estado_actual = eq_estado[eq_estado["codigo"]==codigo]["estado"].values[0]
    return html.Div(children=[
        html.Div(id={"tipo":"cerrar-form","origen":"fondo2"}, n_clicks=0, style={
            "position":"fixed","top":"0","left":"0","width":"100%","height":"100%",
            "backgroundColor":"rgba(8,55,77,0.6)","zIndex":"1100"}),
        html.Div(children=[
            html.Div(children=[
                html.Div(children=[
                    html.Div("CAMBIAR ESTADO OPERATIVO", style={"fontSize":"11px","fontWeight":"700","color":"rgba(255,255,255,0.85)","letterSpacing":"1.2px"}),
                    html.Div(f"{codigo} - {nombre}", style={"fontSize":"15px","fontWeight":"700","color":"white","marginTop":"2px"})
                ]),
                html.Button("X", id={"tipo":"cerrar-form","origen":"boton2"}, n_clicks=0, style={
                    "backgroundColor":"rgba(255,255,255,0.2)","color":"white","border":"none",
                    "borderRadius":"8px","width":"30px","height":"30px","fontSize":"14px","fontWeight":"700","cursor":"pointer"})
            ], style={"display":"flex","justifyContent":"space-between","alignItems":"center",
                      "background":"linear-gradient(120deg, #08374d, #dd9324)","padding":"18px 24px"}),
            html.Div(children=[
                html.Div(f"Estado actual: {estado_actual}", style={"fontSize":"13px","color":"#3f5874","marginBottom":"16px","fontWeight":"600"}),
                html.Label("Nuevo estado operativo", style={"fontSize":"11.5px","fontWeight":"600","color":"#3f5874","marginBottom":"10px","display":"block"}),
                dcc.RadioItems(id="estado-nuevo",
                    options=[{"label":"  Operativo","value":"Operativo"},
                             {"label":"  En reparacion","value":"En reparacion"},
                             {"label":"  Inoperativo","value":"Inoperativo"}],
                    value=estado_actual,
                    labelStyle={"display":"block","padding":"11px 14px","marginBottom":"8px","border":"1.5px solid #e0e7f0",
                                "borderRadius":"9px","fontSize":"13.5px","color":"#08374d","cursor":"pointer","fontWeight":"600"},
                    inputStyle={"marginRight":"8px"}),
                dcc.Store(id="estado-codigo-actual", data=codigo),
                html.Button("Guardar nuevo estado", id="estado-btn-guardar", n_clicks=0, className="boton-hover",
                            style={"width":"100%","height":"46px","backgroundColor":"#dd9324","color":"white",
                                   "border":"none","borderRadius":"10px","fontSize":"14px","fontWeight":"700",
                                   "cursor":"pointer","marginTop":"22px"}),
                html.Div(id="estado-mensaje", style={"fontSize":"12.5px","textAlign":"center","marginTop":"10px","fontWeight":"600"})
            ], style={"padding":"22px 24px"})
        ], style={"position":"fixed","top":"50%","left":"50%","transform":"translate(-50%, -50%)",
                  "backgroundColor":"white","borderRadius":"16px","width":"440px","maxWidth":"94%",
                  "zIndex":"1101","boxShadow":"0 30px 80px rgba(8,55,77,0.45)","overflow":"visible"})
    ])

def formulario_programar_mant(codigo):
    """Formulario modal para programar el proximo mantenimiento de un equipo."""
    nombre = equipos[equipos["codigo"]==codigo]["nombre"].values[0]
    estados = calculos.cargar_estados()
    prox_actual = estados.get(codigo, {}).get("proximo_mant", None)
    return html.Div(children=[
        html.Div(id={"tipo":"cerrar-form","origen":"fondo3"}, n_clicks=0, style={
            "position":"fixed","top":"0","left":"0","width":"100%","height":"100%",
            "backgroundColor":"rgba(8,55,77,0.6)","zIndex":"1100"}),
        html.Div(children=[
            html.Div(children=[
                html.Div(children=[
                    html.Div("PROGRAMAR PROXIMO MANTENIMIENTO", style={"fontSize":"11px","fontWeight":"700","color":"rgba(255,255,255,0.85)","letterSpacing":"1.2px"}),
                    html.Div(f"{codigo} - {nombre}", style={"fontSize":"15px","fontWeight":"700","color":"white","marginTop":"2px"})
                ]),
                html.Button("X", id={"tipo":"cerrar-form","origen":"boton3"}, n_clicks=0, style={
                    "backgroundColor":"rgba(255,255,255,0.2)","color":"white","border":"none",
                    "borderRadius":"8px","width":"30px","height":"30px","fontSize":"14px","fontWeight":"700","cursor":"pointer"})
            ], style={"display":"flex","justifyContent":"space-between","alignItems":"center",
                      "background":"linear-gradient(120deg, #08374d, #13b0a5)","padding":"18px 24px"}),
            html.Div(children=[
                html.Div(f"Programacion actual: {prox_actual if prox_actual else 'No programado'}",
                         style={"fontSize":"13px","color":"#3f5874","marginBottom":"16px","fontWeight":"600"}),
                html.Label("Fecha del proximo mantenimiento", style={"fontSize":"11.5px","fontWeight":"600","color":"#3f5874","marginBottom":"6px","display":"block"}),
                dcc.DatePickerSingle(id="prog-fecha",
                    date=(prox_actual if prox_actual else None),
                    display_format="DD/MM/YYYY",
                    placeholder="Selecciona una fecha",
                    first_day_of_week=1,
                    style={"width":"100%"}),
                dcc.Store(id="prog-codigo-actual", data=codigo),
                html.Button("Guardar programacion", id="prog-btn-guardar", n_clicks=0, className="boton-hover",
                            style={"width":"100%","height":"46px","backgroundColor":"#13b0a5","color":"white",
                                   "border":"none","borderRadius":"10px","fontSize":"14px","fontWeight":"700",
                                   "cursor":"pointer","marginTop":"22px"}),
                html.Div(id="prog-mensaje", style={"fontSize":"12.5px","textAlign":"center","marginTop":"10px","fontWeight":"600"})
            ], style={"padding":"22px 24px"})
        ], style={"position":"fixed","top":"50%","left":"50%","transform":"translate(-50%, -50%)",
                  "backgroundColor":"white","borderRadius":"16px","width":"440px","maxWidth":"94%",
                  "zIndex":"1101","boxShadow":"0 30px 80px rgba(8,55,77,0.45)","overflow":"visible"})
    ])

def seccion_perfil_criticidad(r, color):
    """Construye el desglose del indice de criticidad con las 5 variables ponderadas."""
    variables = [
        ("Funcion clinica", r["v1"], 0.30, "Importancia del equipo para la atencion del paciente"),
        ("Area de uso", r["v2"], 0.25, "Criticidad del area donde opera el equipo"),
        ("Frecuencia de fallas", r["v3"], 0.20, "Historial de fallas correctivas del equipo"),
        ("Antiguedad / vida util", r["v4"], 0.15, "Desgaste segun los anos de uso"),
        ("Costo de reparacion", r["v5"], 0.10, "Impacto economico del mantenimiento"),
    ]
    filas = []
    for nombre_var, valor, peso, descripcion in variables:
        filas.append(html.Div(children=[
            # Encabezado de la variable
            html.Div(children=[
                html.Div(children=[
                    html.Span(nombre_var, style={"fontSize":"12px","fontWeight":"600","color":"#08374d"}),
                    html.Span(f"  (peso {int(peso*100)}%)", style={"fontSize":"11px","color":"#8499b1"})
                ]),
                html.Span(f"{valor}/5", style={"fontSize":"12.5px","fontWeight":"700","color":color,"fontFamily":"monospace"})
            ], style={"display":"flex","justifyContent":"space-between","alignItems":"center","marginBottom":"4px"}),
            # Barra de progreso
            html.Div(html.Div(style={"width":f"{valor/5*100}%","height":"100%","backgroundColor":color,"borderRadius":"30px"}),
                     style={"height":"8px","backgroundColor":"#eef2f7","borderRadius":"30px","overflow":"hidden","marginBottom":"3px"}),
            # Descripcion de la variable
            html.Div(descripcion, style={"fontSize":"10.5px","color":"#8499b1","marginBottom":"12px"})
        ]))

    return html.Div(children=[
        # Explicacion introductoria
        html.Div(children=[
            html.Span("ℹ ", style={"color":color,"fontWeight":"700"}),
            html.Span("El indice de criticidad se calcula ponderando cinco variables. Cada una aporta un peso distinto al resultado final, segun su importancia para la continuidad del servicio clinico.",
                      style={"fontSize":"11.5px","color":"#3f5874"})
        ], style={"backgroundColor":"#f7fafc","border":"1px solid #e0e7f0","borderRadius":"8px","padding":"11px 14px","marginBottom":"16px"}),
        # Desglose de variables
        html.Div(filas),
        # Resultado final del indice
        html.Div(children=[
            html.Div(children=[
                html.Span("Indice de criticidad final", style={"fontSize":"12px","fontWeight":"600","color":"#3f5874"}),
                html.Div(children=[
                    html.Span(str(r["indice"]), style={"fontSize":"26px","fontWeight":"800","color":color}),
                    html.Span(f"/100  -  {r['nivel'].capitalize()}", style={"fontSize":"13px","color":"#8499b1","fontWeight":"600","marginLeft":"4px"})
                ])
            ])
        ], style={"backgroundColor":"#fbfdfe","border":f"1.5px solid {color}","borderRadius":"10px",
                  "padding":"14px 18px","marginTop":"6px","marginBottom":"18px","textAlign":"center"})
    ])

def ficha_equipo_modal(codigo, rol="Visualizacion"):
    """Construye la ventana modal con la ficha del equipo en formato OTM."""
    fila = criticidad[criticidad["cod"]==codigo]
    if len(fila)==0:
        return None
    r = fila.iloc[0]
    color = COLOR_NIVEL[r["nivel"]]
    bg = BG_NIVEL[r["nivel"]]

    # Historial del equipo
    h = historial[historial["codigo_equipo"]==codigo].sort_values("fecha", ascending=False)
    corr = h[h["tipo_mantenimiento"]=="Correctivo"]
    prev = h[h["tipo_mantenimiento"]=="Preventivo"]
    costo_total = h["costo_soles"].sum()
    ultima_fecha = h["fecha"].max()
    ultima_txt = ultima_fecha.strftime("%d/%m/%Y") if pd.notna(ultima_fecha) else "Sin registros"

    # Estado operativo actual (desde calculos)
    eq_estado = calculos.estado_equipos(equipos)
    estado = eq_estado[eq_estado["codigo"]==codigo]["estado"].values[0]
    color_estado = {"Operativo":"#1f9d6b","En reparacion":"#dd9324","Inoperativo":"#d94862"}.get(estado,"#1f9d6b")

    # Calcular indicador de salud del equipo
    salud_pct, salud_label, salud_color = calcular_salud_equipo(r, h, estado)

    return html.Div(children=[
        # Fondo oscurecido
        html.Div(id={"tipo":"cerrar-modal","origen":"fondo"}, n_clicks=0, style={
            "position":"fixed","top":"0","left":"0","width":"100%","height":"100%",
            "backgroundColor":"rgba(8,55,77,0.55)","zIndex":"1000"}),
        # Ventana de la ficha
        html.Div(children=[
            # ===== CABECERA DEL DOCUMENTO =====
            html.Div(children=[
                html.Div(children=[
                    html.Div("FICHA TECNICA DEL EQUIPO", style={"fontSize":"11px","fontWeight":"700",
                             "color":"rgba(255,255,255,0.85)","letterSpacing":"1.5px"}),
                    html.Div(r["nombre"], style={"fontSize":"19px","fontWeight":"700","color":"white","marginTop":"3px"}),
                ]),
                html.Div(children=[
                    html.Div(f"N. {r['cod']}", style={"fontSize":"13px","fontWeight":"700","color":"white","fontFamily":"monospace"}),
                    html.Button("X", id={"tipo":"cerrar-modal","origen":"boton"}, n_clicks=0, style={
                        "backgroundColor":"rgba(255,255,255,0.2)","color":"white","border":"none",
                        "borderRadius":"8px","width":"30px","height":"30px","fontSize":"14px","fontWeight":"700",
                        "cursor":"pointer","marginLeft":"12px"})
                ], style={"display":"flex","alignItems":"center"})
            ], style={"display":"flex","justifyContent":"space-between","alignItems":"center",
                      "background":f"linear-gradient(120deg, #08374d, {color})","padding":"20px 26px"}),

            # ===== CUERPO DEL DOCUMENTO =====
            html.Div(children=[
                # INDICADOR DE SALUD DEL EQUIPO
                html.Div(children=[
                    html.Div(children=[
                        html.Div("Salud del equipo", style={"fontSize":"11px","color":"#8499b1","fontWeight":"600",
                                 "textTransform":"uppercase","letterSpacing":"0.5px"}),
                        html.Div(children=[
                            html.Span(salud_label, style={"fontSize":"16px","fontWeight":"700","color":salud_color}),
                            html.Span(f"  {salud_pct}%", style={"fontSize":"13px","color":"#8499b1","fontFamily":"monospace"})
                        ])
                    ], style={"flex":"1"}),
                    html.Div(html.Div(style={"width":f"{salud_pct}%","height":"100%","backgroundColor":salud_color,
                             "borderRadius":"30px","transition":"width 0.6s"}),
                             style={"flex":"2","height":"12px","backgroundColor":"#eef2f7","borderRadius":"30px","overflow":"hidden"})
                ], style={"display":"flex","alignItems":"center","gap":"16px","backgroundColor":"#fbfdfe",
                          "border":"1px solid #e0e7f0","borderRadius":"10px","padding":"14px 18px","marginBottom":"18px"}),

                # BARRA DE ACCIONES (segun rol)
                barra_acciones_ficha(codigo, rol),

                # SECCION 1: Datos de identificacion
                seccion_titulo("1. Datos de identificacion"),
                html.Div(children=[
                    campo_otm("Codigo", r["cod"]),
                    campo_otm("Marca", r["marca"]),
                    campo_otm("Tipo", r["tipo"]),
                ], style={"display":"flex","gap":"0"}),
                html.Div(children=[
                    campo_otm("Area / Servicio", r["area"]),
                    campo_otm("Ano de adquisicion", str(r["anio"])),
                    campo_otm("Antiguedad", f"{r['antiguedad']} anos"),
                ], style={"display":"flex","gap":"0"}),
                html.Div(children=[
                    campo_otm("Estado operativo", estado, valor_color=color_estado),
                    campo_otm("Nivel de criticidad", r["nivel"].capitalize(), valor_color=color),
                    campo_otm("Vida util estimada", "10 anos"),
                ], style={"display":"flex","gap":"0","marginBottom":"18px"}),

                # SECCION 2: Resumen de mantenimiento
                seccion_titulo("2. Resumen de mantenimiento"),
                html.Div(children=[
                    resumen_otm("Total intervenciones", str(len(h)), "#0d5c7d"),
                    resumen_otm("Preventivos", str(len(prev)), "#1f9d6b"),
                    resumen_otm("Correctivos", str(len(corr)), "#d94862"),
                ], style={"display":"flex","gap":"10px","marginBottom":"10px"}),
                html.Div(children=[
                    resumen_otm("Costo acumulado", f"S/ {costo_total:,.0f}", "#dd9324"),
                    resumen_otm("Ultima intervencion", ultima_txt, "#6c5ce0"),
                ], style={"display":"flex","gap":"10px","marginBottom":"18px"}),

                # SECCION 3: Perfil de criticidad (desglose del indice)
                seccion_titulo("3. Perfil de criticidad"),
                seccion_perfil_criticidad(r, color),

                # SECCION 4: Historial de Ordenes de Trabajo de Mantenimiento (OTM)
                seccion_titulo(f"4. Historial de ordenes de trabajo ({len(h)} registros)"),
                html.Div(children=[
                    tarjeta_otm(reg, idx) for idx, (_, reg) in enumerate(h.iterrows())
                ], style={"display":"flex","flexDirection":"column","gap":"10px"})

            ], style={"padding":"22px 26px","maxHeight":"62vh","overflowY":"auto"}),

            # ===== PIE DEL DOCUMENTO =====
            html.Div(children=[
                html.Span("BioCare Dashboard - Bioingenieros SAC", style={"fontSize":"10.5px","color":"#8499b1","fontWeight":"600"}),
                html.Span(f"Generado: {pd.Timestamp.now().strftime('%d/%m/%Y')}", style={"fontSize":"10.5px","color":"#8499b1"})
            ], style={"display":"flex","justifyContent":"space-between","padding":"12px 26px",
                      "borderTop":"1px solid #e0e7f0","backgroundColor":"#fbfdfe"})
        ], style={"position":"fixed","top":"50%","left":"50%","transform":"translate(-50%, -50%)",
                  "backgroundColor":"white","borderRadius":"16px","width":"620px","maxWidth":"94%",
                  "zIndex":"1001","boxShadow":"0 30px 80px rgba(8,55,77,0.4)","overflow":"hidden"})
    ])

def seccion_titulo(texto):
    return html.Div(texto, style={"fontSize":"12.5px","fontWeight":"700","color":"#08374d",
                    "borderLeft":"3px solid #13b0a5","paddingLeft":"10px","marginBottom":"12px"})

def campo_otm(etiqueta, valor, valor_color="#0b2238"):
    return html.Div(children=[
        html.Div(etiqueta, style={"fontSize":"10px","color":"#8499b1","fontWeight":"600",
                 "textTransform":"uppercase","letterSpacing":"0.3px","marginBottom":"3px"}),
        html.Div(valor, style={"fontSize":"13px","color":valor_color,"fontWeight":"600"})
    ], style={"flex":"1","border":"1px solid #e0e7f0","borderRadius":"0","padding":"10px 13px",
              "backgroundColor":"white"})

def resumen_otm(etiqueta, valor, color):
    return html.Div(children=[
        html.Div(valor, style={"fontSize":"18px","fontWeight":"700","color":color}),
        html.Div(etiqueta, style={"fontSize":"10.5px","color":"#8499b1","marginTop":"2px"})
    ], style={"flex":"1","backgroundColor":"#f7fafc","border":"1px solid #e0e7f0",
              "borderRadius":"10px","padding":"13px 14px","textAlign":"center"})

def tarjeta_otm(reg, idx):
    """Construye una tarjeta tipo Orden de Trabajo de Mantenimiento."""
    es_correctivo = reg["tipo_mantenimiento"] == "Correctivo"
    color_tipo = "#d94862" if es_correctivo else "#1f9d6b"
    bg_tipo = "#fdebef" if es_correctivo else "#e4f7ef"
    fecha = reg["fecha"].strftime("%d/%m/%Y") if pd.notna(reg["fecha"]) else "-"

    # Color de urgencia
    urg = str(reg["urgencia"])
    color_urg = {"Alta":"#d94862","Media":"#dd9324","Baja":"#1f9d6b","Programado":"#0d5c7d"}.get(urg,"#8499b1")

    # Costo formateado
    costo = reg["costo_soles"]
    costo_txt = f"S/ {costo:,.2f}" if pd.notna(costo) else "No registrado"

    return html.Div(children=[
        # Cabecera de la OTM
        html.Div(children=[
            html.Div(children=[
                html.Span(f"OTM-{reg['id_registro']}", style={"fontSize":"11.5px","fontWeight":"700",
                          "color":"#08374d","fontFamily":"monospace"}),
                html.Span(reg["tipo_mantenimiento"], style={"backgroundColor":bg_tipo,"color":color_tipo,
                          "padding":"2px 10px","borderRadius":"20px","fontSize":"10px","fontWeight":"700","marginLeft":"8px"})
            ]),
            html.Span(fecha, style={"fontSize":"11px","color":"#8499b1","fontWeight":"600","fontFamily":"monospace"})
        ], style={"display":"flex","justifyContent":"space-between","alignItems":"center","marginBottom":"8px"}),

        # Descripcion del trabajo
        html.Div(reg["descripcion"], style={"fontSize":"12.5px","fontWeight":"600","color":"#0b2238","marginBottom":"8px"}),

        # Detalles en linea
        html.Div(children=[
            detalle_otm("Categoria", str(reg["categoria_falla"]) if es_correctivo else "Preventivo"),
            detalle_otm("Urgencia", urg, color_urg),
            detalle_otm("Tecnico", str(reg["tecnico"])),
            detalle_otm("Duracion", f"{reg['horas_intervencion']} h"),
            detalle_otm("Costo", costo_txt),
            detalle_otm("Estado final", str(reg["estado_post"])),
        ], style={"display":"flex","flexWrap":"wrap","gap":"16px"})

    ], style={"border":"1px solid #e0e7f0","borderLeft":f"3px solid {color_tipo}",
              "borderRadius":"8px","padding":"13px 16px","backgroundColor":"white"})

def detalle_otm(etiqueta, valor, valor_color="#3f5874"):
    return html.Div(children=[
        html.Span(etiqueta + ": ", style={"fontSize":"10.5px","color":"#8499b1","fontWeight":"600"}),
        html.Span(valor, style={"fontSize":"11.5px","color":valor_color,"fontWeight":"600"})
    ])

def dato_ficha(etiqueta, valor, color):
    return html.Div(children=[
        html.Div(valor, style={"fontSize":"19px","fontWeight":"700","color":color}),
        html.Div(etiqueta, style={"fontSize":"10.5px","color":"#8499b1","marginTop":"2px"})
    ], style={"flex":"1","backgroundColor":"#f7fafc","border":"1px solid #e0e7f0","borderRadius":"10px","padding":"13px 14px","textAlign":"center"})

# --- 5. MODULO 3: ALERTAS ---
def fila_alerta(a, idx, atendida=False):
    color = COLOR_ALERTA[a["nivel"]]
    bg = BG_ALERTA[a["nivel"]]
    # Si esta atendida, se muestra atenuada
    opacidad = "0.55" if atendida else "1"
    return html.Div(children=[
        html.Div(children=[
            html.Div(children=[
                html.Span(a["nivel"], style={"backgroundColor":color,"color":"white",
                          "padding":"3px 10px","borderRadius":"20px","fontSize":"10.5px","fontWeight":"700"}),
                html.Span(f"  {a['equipo']} - {a['nombre']}", style={"fontWeight":"600","color":"#0b2238","fontSize":"13px","marginLeft":"8px"}),
                html.Span("✓ Atendida", style={"color":"#1f9d6b","fontSize":"10.5px","fontWeight":"700","marginLeft":"8px"}) if atendida else None
            ], style={"flex":"1"}),
            # Botones de accion
            html.Div(children=[
                # Boton para abrir la ficha del equipo
                html.Button("Ver ficha", id={"tipo":"alerta-ficha","cod":a["equipo"]}, n_clicks=0,
                            title="Abrir la ficha del equipo",
                            style={"backgroundColor":"white","color":"#0d5c7d","border":"1.5px solid #0d5c7d",
                                   "borderRadius":"7px","padding":"5px 10px","fontSize":"10.5px",
                                   "fontWeight":"700","cursor":"pointer","marginRight":"6px"}),
                # Boton de marcar como atendida
                html.Button("✓" if not atendida else "↺",
                            id={"tipo":"alerta-atender","idx":idx}, n_clicks=0,
                            title="Marcar como atendida" if not atendida else "Reactivar",
                            style={"backgroundColor":"white","color":color,"border":f"1.5px solid {color}",
                                   "borderRadius":"7px","width":"30px","height":"30px","fontSize":"13px",
                                   "fontWeight":"700","cursor":"pointer"})
            ], style={"display":"flex","alignItems":"center"})
        ], style={"display":"flex","justifyContent":"space-between","alignItems":"center"}),
        html.Div(f"{a['tipo']}: {a['detalle']}", style={"fontSize":"12px","color":"#3f5874","marginTop":"5px",
                 "textDecoration":"line-through" if atendida else "none"}),
        # Indicador de antiguedad de la alerta
        html.Div(children=[
            html.Span("🕒 ", style={"fontSize":"10px"}),
            html.Span(f"Generada hace {a.get('antiguedad', 0)} dias" if a.get('antiguedad', 0) > 0 else "Generada recientemente",
                      style={"fontSize":"10.5px","color":"#8499b1","fontWeight":"600"})
        ], style={"marginTop":"4px"})
    ], style={"backgroundColor":bg,"borderLeft":"4px solid "+color,
              "borderRadius":"10px","padding":"13px 16px","marginBottom":"10px","opacity":opacidad})

def contenido_modulo3():
    n_crit = sum(1 for a in lista_alertas if a["nivel"]=="CRITICA")
    n_alta = sum(1 for a in lista_alertas if a["nivel"]=="ALTA")
    n_media = sum(1 for a in lista_alertas if a["nivel"]=="MEDIA")
    # Acciones inmediatas = criticas + altas
    n_inmediata = n_crit + n_alta
    return html.Div(children=[
        html.H2("Sistema de Alertas Automaticas", style={"color":"#08374d","fontWeight":"700","marginBottom":"4px"}),
        html.P("Alertas generadas automaticamente segun reglas de criticidad, mantenimiento vencido y fallas recurrentes.",
               style={"color":"#3f5874","fontSize":"14px","marginBottom":"18px"}),

        # Banner de accion inmediata
        html.Div(children=[
            html.Span("⚠", style={"fontSize":"22px","marginRight":"12px"}),
            html.Div(children=[
                html.Span(f"{n_inmediata} alertas requieren accion inmediata", style={"fontSize":"15px","fontWeight":"700","color":"white"}),
                html.Div(f"{n_crit} criticas y {n_alta} altas necesitan atencion prioritaria del equipo tecnico.",
                         style={"fontSize":"12px","color":"rgba(255,255,255,0.9)","marginTop":"2px"})
            ])
        ], style={"display":"flex","alignItems":"center","background":"linear-gradient(120deg, #d94862, #dd9324)",
                  "borderRadius":"12px","padding":"16px 20px","marginBottom":"20px"}),

        # Tarjetas resumen
        html.Div(children=[
            tarjeta_resumen("CRITICA", n_crit, "Alertas criticas", COLOR_ALERTA, BG_ALERTA),
            tarjeta_resumen("ALTA", n_alta, "Alertas altas", COLOR_ALERTA, BG_ALERTA),
            tarjeta_resumen("MEDIA", n_media, "Alertas medias", COLOR_ALERTA, BG_ALERTA),
        ], style={"display":"flex","gap":"14px","marginBottom":"20px"}),

        # Grafico de distribucion + botones de descarga
        html.Div(children=[
            # Grafico de distribucion
            html.Div(children=[
                html.Div("Distribucion de alertas por tipo", style={"fontSize":"14px","fontWeight":"700","color":"#08374d",
                         "padding":"16px 20px","borderBottom":"1px solid #e0e7f0"}),
                html.Div(dcc.Graph(figure=graficos.grafico_alertas_distribucion(lista_alertas),
                                   config={"displayModeBar":False}), style={"padding":"10px"})
            ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","flex":"2","overflow":"hidden"}),
            # Panel de exportacion
            html.Div(children=[
                html.Div("Exportar reporte de alertas", style={"fontSize":"14px","fontWeight":"700","color":"#08374d",
                         "padding":"16px 20px","borderBottom":"1px solid #e0e7f0"}),
                html.Div(children=[
                    html.P("Descarga el listado completo de alertas activas para reuniones o documentacion.",
                           style={"fontSize":"12px","color":"#8499b1","marginBottom":"16px"}),
                    html.Button("📊  Descargar Excel", id="btn-alertas-excel", n_clicks=0, className="boton-hover",
                                style={"backgroundColor":"#1f9d6b","color":"white","border":"none","borderRadius":"9px",
                                       "padding":"11px 16px","fontSize":"12.5px","fontWeight":"700","cursor":"pointer","width":"100%","marginBottom":"10px"}),
                    html.Button("📄  Descargar PDF", id="btn-alertas-pdf", n_clicks=0, className="boton-hover",
                                style={"backgroundColor":"#d94862","color":"white","border":"none","borderRadius":"9px",
                                       "padding":"11px 16px","fontSize":"12.5px","fontWeight":"700","cursor":"pointer","width":"100%"}),
                    dcc.Download(id="descarga-alertas")
                ], style={"padding":"18px"})
            ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","flex":"1","overflow":"hidden"})
        ], style={"display":"flex","gap":"16px","marginBottom":"20px","alignItems":"flex-start"}),

        html.Div(children=[
            # Lista de alertas con filtros
            html.Div(children=[
                html.Div(children=[
                    html.Span("Alertas activas", style={"fontSize":"14px","fontWeight":"700","color":"#08374d"}),
                    # Filtro por nivel
                    dcc.Dropdown(id="filtro-nivel-alerta",
                        options=[{"label":"Todos los niveles","value":"todos"},
                                 {"label":"Solo criticas","value":"CRITICA"},
                                 {"label":"Solo altas","value":"ALTA"},
                                 {"label":"Solo medias","value":"MEDIA"}],
                        value="todos", clearable=False,
                        style={"fontSize":"12px","width":"180px"})
                ], style={"display":"flex","justifyContent":"space-between","alignItems":"center",
                          "padding":"16px 20px","borderBottom":"1px solid #e0e7f0"}),
                # Buscador y opcion de agrupar
                html.Div(children=[
                    dcc.Input(id="buscador-alertas", type="text",
                              placeholder="🔍  Buscar por equipo o tipo de alerta...",
                              className="login-input",
                              style={"flex":"1","height":"40px","padding":"0 13px","borderRadius":"9px",
                                     "border":"1.5px solid #e0e7f0","fontSize":"12.5px","boxSizing":"border-box","color":"#08374d"}),
                    dcc.Checklist(id="agrupar-alertas",
                        options=[{"label":"  Agrupar por equipo","value":"agrupar"}],
                        value=[], style={"fontSize":"12px","color":"#3f5874","marginLeft":"12px","whiteSpace":"nowrap"},
                        inputStyle={"marginRight":"4px"})
                ], style={"display":"flex","alignItems":"center","padding":"12px 16px 4px"}),
                html.Div(id="lista-alertas",
                         children=[fila_alerta(a, i) for i, a in enumerate(lista_alertas)],
                         style={"padding":"16px","maxHeight":"460px","overflowY":"auto"})
            ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","flex":"1.3","overflow":"hidden"}),
            # Panel de correo
            html.Div(children=[
                html.Div("Notificacion por correo (smtplib)", style={"fontSize":"14px","fontWeight":"700","color":"#08374d",
                         "padding":"16px 20px","borderBottom":"1px solid #e0e7f0"}),
                html.Div(children=[
                    html.P("El sistema puede enviar este reporte por correo automaticamente a los responsables de Bioingenieros SAC e INCOR.",
                           style={"fontSize":"12px","color":"#8499b1","marginBottom":"12px"}),
                    html.Pre(texto_correo, style={"backgroundColor":"#f7fafc","border":"1px solid #e0e7f0",
                             "borderRadius":"10px","padding":"14px","fontSize":"11px","color":"#3f5874",
                             "whiteSpace":"pre-wrap","fontFamily":"monospace","maxHeight":"360px","overflowY":"auto"}),
                    html.Label("Correo destinatario", style={"fontSize":"11.5px","fontWeight":"600","color":"#3f5874","marginTop":"12px","marginBottom":"4px","display":"block"}),
                    dcc.Input(id="correo-destinatario", type="email", value="",
                              placeholder="tu.correo@utec.edu.pe",
                              style={"width":"100%","height":"40px","padding":"0 13px","borderRadius":"9px",
                                     "border":"1.5px solid #e0e7f0","fontSize":"12.5px","boxSizing":"border-box","color":"#08374d"}),
                    html.Button("Enviar reporte por correo", id="btn-correo", n_clicks=0, style={
                        "backgroundColor":"#0d5c7d","color":"white","border":"none","borderRadius":"10px",
                        "padding":"12px 20px","fontSize":"13px","fontWeight":"600","cursor":"pointer","marginTop":"12px","width":"100%"}),
                    html.Div(id="estado-correo", style={"marginTop":"10px","fontSize":"12px"})
                ], style={"padding":"18px"})
            ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","flex":"1","overflow":"hidden"})
        ], style={"display":"flex","gap":"16px","alignItems":"flex-start"})
    ])

# --- 6. MODULO 4: PREDICCION ---
def fila_prediccion(r):
    return html.Tr(children=[
        html.Td(r["cod"], style={"padding":"10px 12px","fontSize":"11px","color":"#8499b1","fontFamily":"monospace"}),
        html.Td(r["nombre"], style={"padding":"10px 12px","fontWeight":"600","color":"#0b2238","fontSize":"12.5px"}),
        html.Td(f"{r['prob_falla']:.1f}%", style={"padding":"10px 12px","fontWeight":"700",
                "color":COLOR_NIVEL[r["nivel_riesgo"]],"fontFamily":"monospace","fontSize":"14px"}),
        html.Td(f"{r['horizonte_dias']} dias", style={"padding":"10px 12px","fontSize":"12px","color":"#3f5874"}),
        html.Td(html.Span(r["nivel_riesgo"].capitalize(), style={
            "backgroundColor":BG_NIVEL[r["nivel_riesgo"]],"color":COLOR_NIVEL[r["nivel_riesgo"]],
            "padding":"3px 11px","borderRadius":"30px","fontSize":"11px","fontWeight":"600"}),
            style={"padding":"10px 12px"})
    ], id={"tipo":"fila-prediccion","codigo":r["cod"]}, className="fila-tabla",
       n_clicks=0, style={"borderBottom":"1px solid #e0e7f0","cursor":"pointer"})

def modal_prediccion(codigo):
    """Construye el modal con el detalle de factores de la prediccion de un equipo."""
    resultado = prediccion.factores_prediccion(prediccion_df, codigo)
    if resultado is None:
        return None
    r, factores = resultado
    color = COLOR_NIVEL[r["nivel_riesgo"]]

    return html.Div(children=[
        html.Div(id={"tipo":"cerrar-pred","origen":"fondo"}, n_clicks=0, style={
            "position":"fixed","top":"0","left":"0","width":"100%","height":"100%",
            "backgroundColor":"rgba(8,55,77,0.55)","zIndex":"1000"}),
        html.Div(children=[
            # Cabecera
            html.Div(children=[
                html.Div(children=[
                    html.Div("ANALISIS PREDICTIVO", style={"fontSize":"11px","fontWeight":"700","color":"rgba(255,255,255,0.85)","letterSpacing":"1.2px"}),
                    html.Div(f"{r['cod']} - {r['nombre']}", style={"fontSize":"17px","fontWeight":"700","color":"white","marginTop":"2px"})
                ]),
                html.Button("X", id={"tipo":"cerrar-pred","origen":"boton"}, n_clicks=0, style={
                    "backgroundColor":"rgba(255,255,255,0.2)","color":"white","border":"none",
                    "borderRadius":"8px","width":"32px","height":"32px","fontSize":"15px","fontWeight":"700","cursor":"pointer"})
            ], style={"display":"flex","justifyContent":"space-between","alignItems":"center",
                      "background":f"linear-gradient(120deg, #08374d, {color})","padding":"20px 26px"}),
            # Cuerpo
            html.Div(children=[
                # Resumen de la prediccion
                html.Div(children=[
                    html.Div(children=[
                        html.Div("Probabilidad de falla", style={"fontSize":"11px","color":"#8499b1","fontWeight":"600"}),
                        html.Div(f"{r['prob_falla']:.1f}%", style={"fontSize":"30px","fontWeight":"800","color":color})
                    ], style={"flex":"1","textAlign":"center"}),
                    html.Div(children=[
                        html.Div("Horizonte estimado", style={"fontSize":"11px","color":"#8499b1","fontWeight":"600"}),
                        html.Div(f"{r['horizonte_dias']} dias", style={"fontSize":"30px","fontWeight":"800","color":"#0d5c7d"})
                    ], style={"flex":"1","textAlign":"center"}),
                    html.Div(children=[
                        html.Div("Nivel de riesgo", style={"fontSize":"11px","color":"#8499b1","fontWeight":"600"}),
                        html.Div(r["nivel_riesgo"].capitalize(), style={"fontSize":"22px","fontWeight":"800","color":color,"marginTop":"5px"})
                    ], style={"flex":"1","textAlign":"center"}),
                ], style={"display":"flex","gap":"12px","backgroundColor":"#f7fafc","border":"1px solid #e0e7f0",
                          "borderRadius":"12px","padding":"18px","marginBottom":"20px"}),

                # Factores que influyen
                seccion_titulo("Factores que influyen en esta prediccion"),
                html.Div(children=[
                    html.Div(children=[
                        html.Div(children=[
                            html.Span(f["nombre"], style={"fontSize":"12.5px","fontWeight":"700","color":"#08374d"}),
                            html.Span(f["impacto"], style={"backgroundColor":f["color"],"color":"white",
                                      "padding":"2px 10px","borderRadius":"20px","fontSize":"10px","fontWeight":"700","float":"right"})
                        ]),
                        html.Div(f["valor"], style={"fontSize":"15px","fontWeight":"700","color":f["color"],"margin":"4px 0"}),
                        html.Div(f["explicacion"], style={"fontSize":"11px","color":"#8499b1"})
                    ], style={"border":"1px solid #e0e7f0","borderLeft":f"3px solid {f['color']}",
                              "borderRadius":"8px","padding":"12px 14px","marginBottom":"10px"})
                    for f in factores
                ]),
                # Recomendacion
                html.Div(children=[
                    html.Span("💡 Recomendacion: ", style={"fontSize":"12px","fontWeight":"700","color":"#08374d"}),
                    html.Span(
                        "Programar mantenimiento preventivo prioritario." if r["nivel_riesgo"]=="ALTO"
                        else ("Mantener vigilancia y revisar en el proximo ciclo." if r["nivel_riesgo"]=="MEDIO"
                              else "El equipo opera dentro de parametros normales."),
                        style={"fontSize":"12px","color":"#3f5874"})
                ], style={"backgroundColor":"#f3f0ff","border":"1px solid #d9d0f5","borderRadius":"10px","padding":"12px 16px","marginTop":"8px"})
            ], style={"padding":"22px 26px","maxHeight":"62vh","overflowY":"auto"})
        ], style={"position":"fixed","top":"50%","left":"50%","transform":"translate(-50%, -50%)",
                  "backgroundColor":"white","borderRadius":"16px","width":"560px","maxWidth":"94%",
                  "zIndex":"1001","boxShadow":"0 30px 80px rgba(8,55,77,0.4)","overflow":"hidden"})
    ])

def seccion_evaluacion_modelo():
    """Construye la seccion con metricas del modelo e importancia de variables."""
    metricas = prediccion.evaluar_modelo(equipos, historial)
    cm = metricas["matriz"]
    return html.Div(children=[
        html.Div(children=[
            # Panel de metricas
            html.Div(children=[
                html.Div("Evaluacion del modelo", style={"fontSize":"14px","fontWeight":"700","color":"#08374d",
                         "padding":"16px 20px","borderBottom":"1px solid #e0e7f0"}),
                html.Div(children=[
                    # Metricas principales
                    html.Div(children=[
                        html.Div(children=[
                            html.Div(f"{metricas['accuracy']}%", style={"fontSize":"28px","fontWeight":"800","color":"#1f9d6b"}),
                            html.Div("Precision (accuracy)", style={"fontSize":"11px","color":"#8499b1","marginTop":"2px"})
                        ], style={"flex":"1","textAlign":"center"}),
                        html.Div(children=[
                            html.Div(f"{metricas['cv']}%", style={"fontSize":"28px","fontWeight":"800","color":"#6c5ce0"}),
                            html.Div("Validacion cruzada", style={"fontSize":"11px","color":"#8499b1","marginTop":"2px"})
                        ], style={"flex":"1","textAlign":"center"}),
                    ], style={"display":"flex","gap":"12px","marginBottom":"18px"}),
                    # Matriz de confusion
                    html.Div("Matriz de confusion", style={"fontSize":"12px","fontWeight":"700","color":"#08374d","marginBottom":"8px"}),
                    html.Table(children=[
                        html.Tr(children=[
                            html.Td("", style={"padding":"6px","fontSize":"10px"}),
                            html.Td("Pred. Normal", style={"padding":"6px 10px","fontSize":"10px","fontWeight":"700","color":"#8499b1","textAlign":"center"}),
                            html.Td("Pred. Riesgo", style={"padding":"6px 10px","fontSize":"10px","fontWeight":"700","color":"#8499b1","textAlign":"center"}),
                        ]),
                        html.Tr(children=[
                            html.Td("Real Normal", style={"padding":"6px 10px","fontSize":"10px","fontWeight":"700","color":"#8499b1"}),
                            html.Td(str(cm[0][0]), style={"padding":"10px","fontSize":"15px","fontWeight":"700","color":"#1f9d6b","textAlign":"center","backgroundColor":"#e4f7ef","borderRadius":"6px"}),
                            html.Td(str(cm[0][1]), style={"padding":"10px","fontSize":"15px","fontWeight":"700","color":"#d94862","textAlign":"center","backgroundColor":"#fdebef","borderRadius":"6px"}),
                        ]),
                        html.Tr(children=[
                            html.Td("Real Riesgo", style={"padding":"6px 10px","fontSize":"10px","fontWeight":"700","color":"#8499b1"}),
                            html.Td(str(cm[1][0]), style={"padding":"10px","fontSize":"15px","fontWeight":"700","color":"#d94862","textAlign":"center","backgroundColor":"#fdebef","borderRadius":"6px"}),
                            html.Td(str(cm[1][1]), style={"padding":"10px","fontSize":"15px","fontWeight":"700","color":"#1f9d6b","textAlign":"center","backgroundColor":"#e4f7ef","borderRadius":"6px"}),
                        ]),
                    ], style={"width":"100%","borderCollapse":"separate","borderSpacing":"4px"}),
                    html.Div("La diagonal verde son los aciertos del modelo; las celdas rojas son los errores.",
                             style={"fontSize":"10.5px","color":"#8499b1","marginTop":"10px","fontStyle":"italic"})
                ], style={"padding":"18px"})
            ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","flex":"1","overflow":"hidden"}),
            # Panel de importancia de variables
            html.Div(children=[
                html.Div("Importancia de las variables", style={"fontSize":"14px","fontWeight":"700","color":"#08374d",
                         "padding":"16px 20px","borderBottom":"1px solid #e0e7f0"}),
                html.Div(dcc.Graph(figure=graficos.grafico_importancia_variables(metricas["importancia"]),
                                   config={"displayModeBar":False}), style={"padding":"10px"})
            ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","flex":"1.2","overflow":"hidden"}),
        ], style={"display":"flex","gap":"16px","marginBottom":"20px","alignItems":"flex-start"})
    ])

def seccion_simulador():
    """Construye el simulador what-if con sliders."""
    # Equipo inicial por defecto (el de mayor riesgo)
    cod_inicial = prediccion_df.iloc[0]["cod"]
    v = prediccion.valores_equipo(prediccion_df, cod_inicial)
    return html.Div(children=[
        html.Div(children=[
            html.Span("🧪  Simulador: que pasaria si...", style={"fontSize":"14px","fontWeight":"700","color":"white"}),
            html.Div("Ajusta los valores de un equipo y observa como cambia su probabilidad de falla en tiempo real",
                     style={"fontSize":"11.5px","color":"rgba(255,255,255,0.85)","marginTop":"2px"})
        ], style={"background":"linear-gradient(120deg, #08374d, #13b0a5)","padding":"16px 20px"}),
        html.Div(children=[
            # Selector de equipo
            html.Label("Selecciona un equipo para simular", style={"fontSize":"12px","fontWeight":"600","color":"#3f5874","marginBottom":"6px","display":"block"}),
            dcc.Dropdown(id="sim-equipo",
                options=[{"label":f"{r['cod']} - {r['nombre']}","value":r["cod"]} for _, r in prediccion_df.iterrows()],
                value=cod_inicial, clearable=False, style={"fontSize":"13px","marginBottom":"18px"}),

            html.Div(children=[
                # Columna de sliders
                html.Div(children=[
                    html.Label("Frecuencia de fallas (por ano)", style={"fontSize":"11.5px","fontWeight":"600","color":"#3f5874"}),
                    dcc.Slider(id="sim-frec", min=0, max=20, step=0.5, value=v["frec_fallas"],
                               marks={0:"0",10:"10",20:"20"}, tooltip={"placement":"bottom","always_visible":False}),
                    html.Label("Dias desde la ultima intervencion", style={"fontSize":"11.5px","fontWeight":"600","color":"#3f5874","marginTop":"14px"}),
                    dcc.Slider(id="sim-dias", min=0, max=120, step=1, value=v["dias_ultima_falla"],
                               marks={0:"0",60:"60",120:"120"}, tooltip={"placement":"bottom","always_visible":False}),
                    html.Label("Antiguedad (anos)", style={"fontSize":"11.5px","fontWeight":"600","color":"#3f5874","marginTop":"14px"}),
                    dcc.Slider(id="sim-antiguedad", min=0, max=15, step=1, value=v["antiguedad"],
                               marks={0:"0",7:"7",15:"15"}, tooltip={"placement":"bottom","always_visible":False}),
                    html.Label("Indice de criticidad", style={"fontSize":"11.5px","fontWeight":"600","color":"#3f5874","marginTop":"14px"}),
                    dcc.Slider(id="sim-indice", min=0, max=100, step=1, value=v["indice_crit"],
                               marks={0:"0",50:"50",100:"100"}, tooltip={"placement":"bottom","always_visible":False}),
                ], style={"flex":"1.4","paddingRight":"24px"}),
                # Columna de resultado
                html.Div(children=[
                    html.Div("Probabilidad de falla simulada", style={"fontSize":"11.5px","color":"#8499b1","fontWeight":"600","textAlign":"center"}),
                    html.Div(id="sim-resultado", children=f"{v['prob_actual']:.1f}%",
                             style={"fontSize":"44px","fontWeight":"800","color":COLOR_NIVEL["ALTO"],"textAlign":"center","margin":"8px 0"}),
                    html.Div(id="sim-nivel", children="Nivel ALTO",
                             style={"fontSize":"13px","fontWeight":"700","textAlign":"center","marginBottom":"12px"}),
                    html.Div(id="sim-comparacion", style={"fontSize":"11.5px","color":"#8499b1","textAlign":"center"})
                ], style={"flex":"1","backgroundColor":"#f7fafc","border":"1px solid #e0e7f0","borderRadius":"12px",
                          "padding":"20px","display":"flex","flexDirection":"column","justifyContent":"center"})
            ], style={"display":"flex","alignItems":"flex-start"}),
            # Guardar costo del equipo (no editable en sliders, pero necesario para predecir)
            dcc.Store(id="sim-costo", data=v["costo_prom"]),
            dcc.Store(id="sim-prob-actual", data=v["prob_actual"])
        ], style={"padding":"20px"})
    ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","overflow":"hidden","marginBottom":"20px"})

def tarjeta_comparacion(codigo):
    """Construye una tarjeta con el perfil de prediccion de un equipo para comparar."""
    fila = prediccion_df[prediccion_df["cod"]==codigo]
    if len(fila) == 0:
        return html.Div("Equipo no encontrado")
    r = fila.iloc[0]
    color = COLOR_NIVEL[r["nivel_riesgo"]]
    filas_datos = [
        ("Probabilidad de falla", f"{r['prob_falla']:.1f}%", color),
        ("Nivel de riesgo", r["nivel_riesgo"].capitalize(), color),
        ("Horizonte estimado", f"{r['horizonte_dias']} dias", "#0d5c7d"),
        ("Frecuencia de fallas", f"{r['frec_fallas']:.1f}/ano", "#3f5874"),
        ("Dias sin intervencion", f"{int(r['dias_ultima_falla'])} dias", "#3f5874"),
        ("Antiguedad", f"{int(r['antiguedad'])} anos", "#3f5874"),
        ("Indice de criticidad", f"{int(r['indice_crit'])}/100", "#3f5874"),
        ("Costo promedio", f"S/ {r['costo_prom']:.0f}", "#3f5874"),
    ]
    return html.Div(children=[
        html.Div(children=[
            html.Div(r["cod"], style={"fontSize":"11px","color":"rgba(255,255,255,0.85)","fontFamily":"monospace"}),
            html.Div(r["nombre"], style={"fontSize":"14px","fontWeight":"700","color":"white","marginTop":"2px"})
        ], style={"background":f"linear-gradient(120deg, #08374d, {color})","padding":"14px 16px"}),
        html.Div(children=[
            html.Div(children=[
                html.Span(etiqueta, style={"fontSize":"11.5px","color":"#8499b1"}),
                html.Span(valor, style={"fontSize":"13px","fontWeight":"700","color":col,"float":"right"})
            ], style={"padding":"9px 4px","borderBottom":"1px solid #eef2f7"})
            for etiqueta, valor, col in filas_datos
        ], style={"padding":"12px 16px"})
    ], style={"backgroundColor":"white","border":"1px solid #e0e7f0","borderRadius":"12px","flex":"1","overflow":"hidden"})

def seccion_comparacion():
    """Construye la seccion de comparacion de equipos lado a lado."""
    cod1 = prediccion_df.iloc[0]["cod"]
    cod2 = prediccion_df.iloc[1]["cod"]
    opciones = [{"label":f"{r['cod']} - {r['nombre']}","value":r["cod"]} for _, r in prediccion_df.iterrows()]
    return html.Div(children=[
        html.Div(children=[
            html.Span("⚖️  Comparacion de equipos lado a lado", style={"fontSize":"14px","fontWeight":"700","color":"white"}),
            html.Div("Selecciona dos equipos para comparar sus perfiles de riesgo",
                     style={"fontSize":"11.5px","color":"rgba(255,255,255,0.85)","marginTop":"2px"})
        ], style={"background":"linear-gradient(120deg, #08374d, #dd9324)","padding":"16px 20px"}),
        html.Div(children=[
            html.Div(children=[
                html.Div(children=[
                    html.Label("Equipo A", style={"fontSize":"12px","fontWeight":"600","color":"#3f5874","marginBottom":"6px","display":"block"}),
                    dcc.Dropdown(id="comp-equipo-1", options=opciones, value=cod1, clearable=False, style={"fontSize":"12.5px"})
                ], style={"flex":"1","marginRight":"12px"}),
                html.Div(children=[
                    html.Label("Equipo B", style={"fontSize":"12px","fontWeight":"600","color":"#3f5874","marginBottom":"6px","display":"block"}),
                    dcc.Dropdown(id="comp-equipo-2", options=opciones, value=cod2, clearable=False, style={"fontSize":"12.5px"})
                ], style={"flex":"1"}),
            ], style={"display":"flex","marginBottom":"18px"}),
            html.Div(id="comp-resultado", children=html.Div(children=[
                tarjeta_comparacion(cod1), tarjeta_comparacion(cod2)
            ], style={"display":"flex","gap":"14px"}))
        ], style={"padding":"20px"})
    ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","overflow":"hidden","marginBottom":"20px"})

def contenido_modulo4():
    n_alto = (prediccion_df["nivel_riesgo"]=="ALTO").sum()
    n_medio = (prediccion_df["nivel_riesgo"]=="MEDIO").sum()
    n_bajo = (prediccion_df["nivel_riesgo"]=="BAJO").sum()
    return html.Div(children=[
        html.H2("Modelo Predictivo de Fallas", style={"color":"#08374d","fontWeight":"700","marginBottom":"4px"}),
        html.P("Estimacion de la probabilidad de falla en los proximos 30-60 dias mediante regresion logistica.",
               style={"color":"#3f5874","fontSize":"14px","marginBottom":"20px"}),

        # Banner explicativo del modelo
        html.Div(children=[
            html.Span("🔮 ", style={"fontSize":"18px"}),
            html.Span("El modelo analiza 5 caracteristicas de cada equipo para estimar su riesgo de falla. Los equipos en rojo requieren mantenimiento preventivo prioritario.",
                      style={"fontSize":"12.5px","color":"#3f5874"})
        ], style={"backgroundColor":"#f3f0ff","border":"1px solid #d9d0f5","borderRadius":"10px","padding":"12px 16px","marginBottom":"20px"}),

        # Tarjetas resumen
        html.Div(children=[
            tarjeta_resumen("ALTO", n_alto, "Riesgo alto (>= 70%)", COLOR_NIVEL, BG_NIVEL),
            tarjeta_resumen("MEDIO", n_medio, "Riesgo medio (40-69%)", COLOR_NIVEL, BG_NIVEL),
            tarjeta_resumen("BAJO", n_bajo, "Riesgo bajo (< 40%)", COLOR_NIVEL, BG_NIVEL),
        ], style={"display":"flex","gap":"14px","marginBottom":"20px"}),

        # Filtro por nivel de riesgo
        html.Div(children=[
            html.Span("Filtrar por nivel de riesgo:", style={"fontSize":"12.5px","fontWeight":"600","color":"#3f5874","marginRight":"12px"}),
            dcc.Dropdown(id="filtro-riesgo-pred",
                options=[{"label":"Todos los niveles","value":"todos"},
                         {"label":"Solo riesgo alto","value":"ALTO"},
                         {"label":"Solo riesgo medio","value":"MEDIO"},
                         {"label":"Solo riesgo bajo","value":"BAJO"}],
                value="todos", clearable=False,
                style={"fontSize":"13px","width":"240px"})
        ], style={"display":"flex","alignItems":"center","marginBottom":"20px","backgroundColor":"white",
                  "padding":"14px 18px","borderRadius":"12px","boxShadow":"0 4px 16px rgba(8,55,77,0.06)"}),

        # Graficos de prediccion
        html.Div(children=[
            html.Div(children=[
                html.Div("Top 10 equipos por probabilidad de falla", style={"fontSize":"14px","fontWeight":"700","color":"#08374d",
                         "padding":"16px 20px","borderBottom":"1px solid #e0e7f0"}),
                html.Div(dcc.Graph(figure=graficos.grafico_prediccion_riesgo(prediccion_df),
                                   config={"displayModeBar":False}), style={"padding":"10px"})
            ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","flex":"1","overflow":"hidden"}),
            html.Div(children=[
                html.Div("Mapa de riesgo: frecuencia vs inactividad", style={"fontSize":"14px","fontWeight":"700","color":"#08374d",
                         "padding":"16px 20px","borderBottom":"1px solid #e0e7f0"}),
                html.Div(dcc.Graph(figure=graficos.grafico_prediccion_dispersion(prediccion_df),
                                   config={"displayModeBar":False}), style={"padding":"10px"})
            ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","flex":"1","overflow":"hidden"}),
        ], style={"display":"flex","gap":"16px","marginBottom":"20px"}),

        # Seccion de evaluacion del modelo
        seccion_evaluacion_modelo(),

        # Tabla de prediccion (clicable para ver factores, filtrable)
        html.Div(children=[
            html.Div("Prediccion detallada por equipo (haz clic en una fila para ver los factores)", style={"fontSize":"14px","fontWeight":"700",
                     "color":"#08374d","padding":"16px 20px","borderBottom":"1px solid #e0e7f0"}),
            html.Div(html.Table(children=[
                html.Thead(html.Tr(children=[
                    html.Th(h, style={"backgroundColor":"#08374d","color":"white","padding":"11px 12px",
                            "textAlign":"left","fontSize":"10.5px","textTransform":"uppercase"})
                    for h in ["Codigo","Equipo","Probabilidad","Horizonte","Riesgo"]])),
                html.Tbody(id="cuerpo-tabla-pred", children=[fila_prediccion(r) for _, r in prediccion_df.iterrows()])
            ], style={"width":"100%","borderCollapse":"collapse"}), style={"padding":"0 8px 8px"})
        ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","overflow":"hidden","marginBottom":"20px"}),

        # Cronograma de mantenimiento sugerido
        html.Div(children=[
            html.Div(children=[
                html.Span("📅  Cronograma de mantenimiento sugerido", style={"fontSize":"14px","fontWeight":"700","color":"white"}),
                html.Div("Generado automaticamente por el modelo, priorizando los equipos de mayor riesgo",
                         style={"fontSize":"11.5px","color":"rgba(255,255,255,0.85)","marginTop":"2px"})
            ], style={"background":"linear-gradient(120deg, #08374d, #6c5ce0)","padding":"16px 20px"}),
            html.Div(id="cronograma-pred", children=construir_cronograma(prediccion_df), style={"padding":"16px"})
        ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","overflow":"hidden","marginBottom":"20px"}),

        # Simulador what-if
        seccion_simulador(),

        # Comparacion de equipos lado a lado
        seccion_comparacion(),

        # Descarga del reporte de prediccion
        html.Div(children=[
            html.Div("Exportar reporte de prediccion", style={"fontSize":"14px","fontWeight":"700","color":"#08374d",
                     "padding":"16px 20px","borderBottom":"1px solid #e0e7f0"}),
            html.Div(children=[
                html.P("Descarga el analisis predictivo completo de los 30 equipos para documentacion o reuniones.",
                       style={"fontSize":"12px","color":"#8499b1","marginBottom":"14px"}),
                html.Div(children=[
                    html.Button("📊  Descargar Excel", id="btn-pred-excel", n_clicks=0, className="boton-hover",
                                style={"backgroundColor":"#1f9d6b","color":"white","border":"none","borderRadius":"9px",
                                       "padding":"11px 18px","fontSize":"12.5px","fontWeight":"700","cursor":"pointer","marginRight":"10px"}),
                    html.Button("📄  Descargar PDF", id="btn-pred-pdf", n_clicks=0, className="boton-hover",
                                style={"backgroundColor":"#d94862","color":"white","border":"none","borderRadius":"9px",
                                       "padding":"11px 18px","fontSize":"12.5px","fontWeight":"700","cursor":"pointer"}),
                    dcc.Download(id="descarga-prediccion")
                ], style={"display":"flex"})
            ], style={"padding":"18px"})
        ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","overflow":"hidden","marginBottom":"20px"}),

        html.Div("Nota: el modelo usa regresion logistica entrenada sobre las caracteristicas de cada equipo (frecuencia de fallas, dias desde la ultima falla, antiguedad, indice de criticidad y costo promedio).",
                 style={"fontSize":"11.5px","color":"#8499b1","marginTop":"14px","fontStyle":"italic"})
    ])

def construir_cronograma(pred_df):
    """Construye la lista del cronograma de mantenimiento sugerido."""
    crono = prediccion.cronograma_mantenimiento(pred_df, 8)
    if not crono:
        return [html.Div("No hay equipos para programar.", style={"textAlign":"center","color":"#8499b1","padding":"20px","fontSize":"13px"})]
    filas = []
    for c in crono:
        color = COLOR_NIVEL[c["nivel"]]
        filas.append(html.Div(children=[
            html.Div(children=[
                html.Span(f"#{c['prioridad']}", style={"backgroundColor":color,"color":"white","borderRadius":"50%",
                          "width":"26px","height":"26px","display":"inline-flex","alignItems":"center",
                          "justifyContent":"center","fontSize":"12px","fontWeight":"700","marginRight":"12px"}),
                html.Span(c["cod"], style={"fontSize":"11px","color":"#8499b1","fontFamily":"monospace","marginRight":"8px"}),
                html.Span(c["nombre"][:30], style={"fontSize":"12.5px","color":"#0b2238","fontWeight":"600"})
            ], style={"display":"flex","alignItems":"center","flex":"1"}),
            html.Div(children=[
                html.Span(c["nivel"], style={"backgroundColor":BG_NIVEL[c["nivel"]],"color":color,
                          "padding":"2px 10px","borderRadius":"20px","fontSize":"10px","fontWeight":"700","marginRight":"12px"}),
                html.Span(f"📅 {c['fecha']}", style={"fontSize":"12px","color":"#3f5874","fontWeight":"600","fontFamily":"monospace"})
            ], style={"display":"flex","alignItems":"center"})
        ], style={"display":"flex","justifyContent":"space-between","alignItems":"center",
                  "padding":"12px 14px","borderBottom":"1px solid #eef2f7"}))
    return filas


# --- 6b. MODULO 5: AUTOMATIZACION DE MANTENIMIENTOS ---
def panel_anomalias():
    """Panel que muestra los equipos con comportamiento atipico (anomalias)."""
    anomalias = automatizacion.detectar_anomalias(equipos, historial)
    if not anomalias:
        contenido = html.Div("No se detectaron anomalias en el parque. Todos los equipos operan dentro de sus patrones historicos.",
                             style={"fontSize":"13px","color":"#1f9d6b","padding":"10px 0"})
    else:
        tarjetas = []
        for a in anomalias:
            tarjetas.append(html.Div(children=[
                html.Div(children=[
                    html.Span(a["cod"], style={"fontSize":"11px","color":"#8499b1","fontFamily":"monospace"}),
                    html.Span(f"  {a['ratio']}x", style={"fontSize":"16px","fontWeight":"800","color":"#d94862","float":"right"})
                ]),
                html.Div(a["nombre"][:28], style={"fontSize":"12.5px","fontWeight":"600","color":"#0b2238","margin":"4px 0"}),
                html.Div(f"{a['tasa_reciente']} fallas recientes vs {a['tasa_historica']}/trim. historico",
                         style={"fontSize":"10.5px","color":"#8499b1"})
            ], style={"backgroundColor":"white","border":"1px solid #f0d0d6","borderLeft":"3px solid #d94862",
                      "borderRadius":"10px","padding":"12px 14px","flex":"1","minWidth":"180px"}))
        contenido = html.Div(tarjetas, style={"display":"flex","gap":"12px","flexWrap":"wrap"})

    return html.Div(children=[
        html.Div(children=[
            html.Span("🔍  Deteccion de anomalias", style={"fontSize":"15px","fontWeight":"700","color":"white"}),
            html.Div("Equipos cuya frecuencia de fallas se ha acelerado respecto a su patron historico",
                     style={"fontSize":"12px","color":"rgba(255,255,255,0.85)","marginTop":"2px"})
        ], style={"background":"linear-gradient(120deg, #08374d, #d94862)","padding":"16px 20px"}),
        html.Div(contenido, style={"padding":"18px 20px"})
    ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","overflow":"hidden","marginBottom":"22px"})

def contenido_modulo5():
    return html.Div(children=[
        html.H2("Automatizacion de Mantenimientos", style={"color":"#08374d","fontWeight":"700","marginBottom":"4px"}),
        html.P("Reemplaza la busqueda manual del SISMAC: clasificacion automatica de fallas con IA, "
               "consulta instantanea del historial y resumen automatico por equipo.",
               style={"color":"#3f5874","fontSize":"14px","marginBottom":"22px"}),

        # PANEL DE DETECCION DE ANOMALIAS
        panel_anomalias(),

        # CLASIFICADOR ML
        html.Div(children=[
            html.Div(children=[
                html.Span("Clasificador Inteligente de Fallas", style={"fontSize":"15px","fontWeight":"700","color":"white"}),
                html.Span(f"  Precision: {clf_acc}%", style={"fontSize":"12px","color":"#b8e6d3","marginLeft":"10px"})
            ], style={"marginBottom":"6px"}),
            html.P("Escribe la descripcion de una falla y el sistema la clasifica automaticamente en una de las 6 categorias.",
                   style={"fontSize":"12.5px","color":"#cfe6ec","marginBottom":"14px"}),

            # Metricas del clasificador
            html.Div(children=[
                html.Div(children=[
                    html.Span(f"{clf_acc}%", style={"fontSize":"20px","fontWeight":"800","color":"white"}),
                    html.Div("Precision (test)", style={"fontSize":"10.5px","color":"#cfe6ec"})
                ], style={"flex":"1","textAlign":"center","backgroundColor":"rgba(255,255,255,0.12)","borderRadius":"10px","padding":"10px"}),
                html.Div(children=[
                    html.Span(f"{clf_cv}%", style={"fontSize":"20px","fontWeight":"800","color":"white"}),
                    html.Div("Validacion cruzada", style={"fontSize":"10.5px","color":"#cfe6ec"})
                ], style={"flex":"1","textAlign":"center","backgroundColor":"rgba(255,255,255,0.12)","borderRadius":"10px","padding":"10px"}),
                html.Div(children=[
                    html.Span("6", style={"fontSize":"20px","fontWeight":"800","color":"white"}),
                    html.Div("Categorias", style={"fontSize":"10.5px","color":"#cfe6ec"})
                ], style={"flex":"1","textAlign":"center","backgroundColor":"rgba(255,255,255,0.12)","borderRadius":"10px","padding":"10px"}),
                html.Div(children=[
                    html.Span("TF-IDF", style={"fontSize":"15px","fontWeight":"800","color":"white","lineHeight":"26px"}),
                    html.Div("Tecnica NLP", style={"fontSize":"10.5px","color":"#cfe6ec"})
                ], style={"flex":"1","textAlign":"center","backgroundColor":"rgba(255,255,255,0.12)","borderRadius":"10px","padding":"10px"}),
            ], style={"display":"flex","gap":"10px","marginBottom":"16px"}),

            html.Div(children=[
                dcc.Input(id="input-falla", type="text", placeholder="Ej.: la pantalla se queda congelada y no responde",
                          style={"flex":"1","height":"46px","lineHeight":"46px","padding":"0 16px","borderRadius":"10px","border":"none","fontSize":"14px","color":"#08374d","backgroundColor":"white","boxSizing":"border-box","fontFamily":"Segoe UI, sans-serif"}),
                html.Button("Clasificar", id="btn-clasificar", n_clicks=0, style={
                    "backgroundColor":"white","color":"#0d5c7d","border":"none","borderRadius":"10px",
                    "padding":"0 24px","height":"46px","fontSize":"14px","fontWeight":"700","cursor":"pointer","marginLeft":"10px","boxSizing":"border-box"})
            ], style={"display":"flex"}),

            # Ejemplos rapidos
            html.Div(children=[
                html.Span("Ejemplos rapidos: ", style={"fontSize":"11.5px","color":"#cfe6ec","marginRight":"6px"}),
                html.Button("No enciende", id={"tipo":"ejemplo-falla","texto":"el equipo no enciende ni con el cargador"}, n_clicks=0, style=ESTILO_CHIP),
                html.Button("Pantalla congelada", id={"tipo":"ejemplo-falla","texto":"la pantalla se queda congelada y no responde"}, n_clicks=0, style=ESTILO_CHIP),
                html.Button("Lectura erronea", id={"tipo":"ejemplo-falla","texto":"marca valores de presion incorrectos"}, n_clicks=0, style=ESTILO_CHIP),
                html.Button("Ruido extrano", id={"tipo":"ejemplo-falla","texto":"hace un ruido extrano y vibra"}, n_clicks=0, style=ESTILO_CHIP),
            ], style={"marginTop":"12px","display":"flex","alignItems":"center","flexWrap":"wrap","gap":"6px"}),

            html.Div(id="resultado-clasificacion", style={"marginTop":"16px"})
        ], style={"background":"linear-gradient(135deg, #08374d, #13b0a5)","borderRadius":"14px","padding":"24px","marginBottom":"22px"}),

        # CLASIFICACION POR LOTE
        html.Div(children=[
            html.Div(children=[
                html.Span("📋  Clasificacion por lote", style={"fontSize":"15px","fontWeight":"700","color":"#08374d"}),
                html.Div("Pega varias descripciones de falla (una por linea) y el sistema las clasifica todas a la vez",
                         style={"fontSize":"12px","color":"#8499b1","marginTop":"2px"})
            ], style={"padding":"16px 20px","borderBottom":"1px solid #e0e7f0"}),
            html.Div(children=[
                dcc.Textarea(id="input-lote",
                    placeholder="Ejemplo:\nla pantalla no enciende\nel sensor marca valores erroneos\nhace ruido al funcionar\nse reinicia solo constantemente",
                    style={"width":"100%","height":"120px","padding":"12px","borderRadius":"10px","border":"1.5px solid #e0e7f0",
                           "fontSize":"13px","color":"#08374d","fontFamily":"Segoe UI, sans-serif","boxSizing":"border-box","resize":"vertical"}),
                html.Button("Clasificar lote", id="btn-lote", n_clicks=0, className="boton-hover",
                            style={"backgroundColor":"#13b0a5","color":"white","border":"none","borderRadius":"10px",
                                   "padding":"11px 22px","fontSize":"13px","fontWeight":"700","cursor":"pointer","marginTop":"12px"}),
                html.Div(id="resultado-lote", style={"marginTop":"16px"})
            ], style={"padding":"20px"})
        ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","overflow":"hidden","marginBottom":"22px"}),

        # CONSULTA DE HISTORIAL
        html.Div(children=[
            html.Div("Consulta instantanea de historial", style={"fontSize":"14px","fontWeight":"700",
                     "color":"#08374d","marginBottom":"12px"}),
            dcc.Dropdown(id="dropdown-equipo", options=[{"label":f"{c} - {equipos[equipos['codigo']==c]['nombre'].values[0]}","value":c} for c in lista_codigos],
                         placeholder="Selecciona un equipo para ver su informacion", style={"marginBottom":"16px"}),
            html.Div(id="info-equipo")
        ], style={"backgroundColor":"white","borderRadius":"14px","padding":"22px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","marginBottom":"22px"}),

        # ESTADISTICAS GLOBALES DEL PARQUE
        seccion_estadisticas_globales(),

        # ANALISIS TEMPORAL Y POR AREAS
        seccion_analisis_avanzado(),

        # EXPORTACION DEL REPORTE DE AUTOMATIZACION
        html.Div(children=[
            html.Div("Exportar reporte de automatizacion", style={"fontSize":"14px","fontWeight":"700","color":"#08374d",
                     "padding":"16px 20px","borderBottom":"1px solid #e0e7f0"}),
            html.Div(children=[
                html.P("Descarga el analisis completo del modulo: estadisticas globales de fallas, anomalias detectadas y distribucion por categoria.",
                       style={"fontSize":"12px","color":"#8499b1","marginBottom":"14px"}),
                html.Div(children=[
                    html.Button("📊  Descargar Excel", id="btn-autom-excel", n_clicks=0, className="boton-hover",
                                style={"backgroundColor":"#1f9d6b","color":"white","border":"none","borderRadius":"9px",
                                       "padding":"11px 18px","fontSize":"12.5px","fontWeight":"700","cursor":"pointer","marginRight":"10px"}),
                    html.Button("📄  Descargar PDF", id="btn-autom-pdf", n_clicks=0, className="boton-hover",
                                style={"backgroundColor":"#d94862","color":"white","border":"none","borderRadius":"9px",
                                       "padding":"11px 18px","fontSize":"12.5px","fontWeight":"700","cursor":"pointer"}),
                    dcc.Download(id="descarga-automatizacion")
                ], style={"display":"flex"})
            ], style={"padding":"18px"})
        ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","overflow":"hidden","marginBottom":"14px"})
    ])

def seccion_analisis_avanzado():
    """Seccion con el analisis de tendencia temporal y el comparador por areas."""
    return html.Div(children=[
        html.Div(children=[
            # Tendencia temporal de fallas
            html.Div(children=[
                html.Div(children=[
                    html.Span("📈  Tendencia temporal de fallas", style={"fontSize":"14px","fontWeight":"700","color":"white"}),
                    html.Div("Evolucion de cada categoria de falla a lo largo de los anos",
                             style={"fontSize":"11px","color":"rgba(255,255,255,0.85)","marginTop":"2px"})
                ], style={"background":"linear-gradient(120deg, #08374d, #13b0a5)","padding":"14px 18px"}),
                html.Div(dcc.Graph(figure=graficos.grafico_tendencia_fallas(historial), config={"displayModeBar":False}),
                         style={"padding":"12px"})
            ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","flex":"1","overflow":"hidden"}),
        ], style={"marginBottom":"16px"}),
        # Comparador por areas
        html.Div(children=[
            html.Div(children=[
                html.Span("🏥  Comparador de fallas por area clinica", style={"fontSize":"14px","fontWeight":"700","color":"white"}),
                html.Div("Distribucion de las categorias de falla en cada area del instituto",
                         style={"fontSize":"11px","color":"rgba(255,255,255,0.85)","marginTop":"2px"})
            ], style={"background":"linear-gradient(120deg, #08374d, #dd9324)","padding":"14px 18px"}),
            html.Div(dcc.Graph(figure=graficos.grafico_fallas_por_area(equipos, historial), config={"displayModeBar":False}),
                     style={"padding":"12px"})
        ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","overflow":"hidden","marginBottom":"14px"})
    ])

def seccion_estadisticas_globales():
    """Construye la seccion de estadisticas globales de fallas del parque."""
    stats = automatizacion.estadisticas_globales(historial)
    return html.Div(children=[
        html.Div(children=[
            html.Span("📊  Estadisticas globales de fallas del parque", style={"fontSize":"15px","fontWeight":"700","color":"white"}),
            html.Div(f"Analisis de las {stats['total_fallas']} fallas correctivas registradas en los 30 equipos",
                     style={"fontSize":"12px","color":"rgba(255,255,255,0.85)","marginTop":"2px"})
        ], style={"background":"linear-gradient(120deg, #08374d, #6c5ce0)","padding":"16px 20px"}),
        html.Div(children=[
            # Tarjetas de resumen
            html.Div(children=[
                html.Div(children=[
                    html.Div(str(stats["total_fallas"]), style={"fontSize":"24px","fontWeight":"800","color":"#d94862"}),
                    html.Div("Fallas correctivas", style={"fontSize":"11px","color":"#8499b1"})
                ], style={"flex":"1","textAlign":"center","backgroundColor":"#fbfdfe","borderRadius":"10px","padding":"14px","border":"1px solid #e0e7f0"}),
                html.Div(children=[
                    html.Div(stats["categoria_top"], style={"fontSize":"18px","fontWeight":"800","color":"#6c5ce0","lineHeight":"30px"}),
                    html.Div("Categoria mas comun", style={"fontSize":"11px","color":"#8499b1"})
                ], style={"flex":"1","textAlign":"center","backgroundColor":"#fbfdfe","borderRadius":"10px","padding":"14px","border":"1px solid #e0e7f0"}),
                html.Div(children=[
                    html.Div(f"S/ {stats['costo_total']/1000:.0f}k", style={"fontSize":"24px","fontWeight":"800","color":"#1f9d6b"}),
                    html.Div("Costo total correctivo", style={"fontSize":"11px","color":"#8499b1"})
                ], style={"flex":"1","textAlign":"center","backgroundColor":"#fbfdfe","borderRadius":"10px","padding":"14px","border":"1px solid #e0e7f0"}),
                html.Div(children=[
                    html.Div("6", style={"fontSize":"24px","fontWeight":"800","color":"#0d5c7d"}),
                    html.Div("Categorias de falla", style={"fontSize":"11px","color":"#8499b1"})
                ], style={"flex":"1","textAlign":"center","backgroundColor":"#fbfdfe","borderRadius":"10px","padding":"14px","border":"1px solid #e0e7f0"}),
            ], style={"display":"flex","gap":"12px","marginBottom":"18px"}),
            # Graficos
            html.Div(children=[
                html.Div(children=[
                    html.Div("Cantidad de fallas por categoria", style={"fontSize":"13px","fontWeight":"700","color":"#08374d","marginBottom":"8px"}),
                    dcc.Graph(figure=graficos.grafico_estadisticas_globales(stats["categorias"]), config={"displayModeBar":False})
                ], style={"flex":"1.3","backgroundColor":"#fbfdfe","borderRadius":"10px","padding":"16px","border":"1px solid #e0e7f0"}),
                html.Div(children=[
                    html.Div("Distribucion del costo por categoria", style={"fontSize":"13px","fontWeight":"700","color":"#08374d","marginBottom":"8px"}),
                    dcc.Graph(figure=graficos.grafico_costo_categoria(stats["categorias"]), config={"displayModeBar":False})
                ], style={"flex":"1","backgroundColor":"#fbfdfe","borderRadius":"10px","padding":"16px","border":"1px solid #e0e7f0"}),
            ], style={"display":"flex","gap":"14px"})
        ], style={"padding":"20px"})
    ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","overflow":"hidden","marginBottom":"14px"})


# --- 6c. PANTALLA DE INICIO (Resumen ejecutivo) ---
def tarjeta_inicio(icono, etiqueta, valor, descripcion, color, tendencia):
    """Tarjeta del inicio con un indicador de mini-tendencia."""
    texto_tend, color_tend = tendencia
    return html.Div(children=[
        html.Div(icono, style={"fontSize":"22px","marginBottom":"10px"}),
        html.Div(etiqueta, style={"fontSize":"12px","color":"#8499b1","fontWeight":"600",
                                  "textTransform":"uppercase","letterSpacing":"0.5px","minHeight":"32px"}),
        html.Div(valor, style={"fontSize":"32px","fontWeight":"700","color":color}),
        html.Div(descripcion, style={"fontSize":"11.5px","color":"#8499b1","marginTop":"6px"}),
        # Mini-tendencia
        html.Div(children=[
            html.Span("● ", style={"fontSize":"9px","color":color_tend}),
            html.Span(texto_tend, style={"fontSize":"10.5px","color":color_tend,"fontWeight":"600"})
        ], style={"marginTop":"8px","borderTop":"1px solid #eef2f7","paddingTop":"8px"})
    ], className="tarjeta-hover", style={"backgroundColor":"white","padding":"22px","borderRadius":"14px",
              "boxShadow":"0 4px 16px rgba(8,55,77,0.08)","flex":"1","minWidth":"200px","borderTop":"3px solid "+color})

def _tendencia_disponibilidad():
    """Calcula una mini-tendencia para la disponibilidad."""
    if disponibilidad >= 85:
        return ("Por encima de la meta (85%)", "#1f9d6b")
    elif disponibilidad >= 75:
        return ("Cerca de la meta (85%)", "#dd9324")
    else:
        return ("Por debajo de la meta", "#d94862")

def _tendencia_alertas():
    """Calcula una mini-tendencia para las alertas."""
    n_crit = sum(1 for a in lista_alertas if a["nivel"]=="CRITICA")
    if n_crit > 0:
        return (f"{n_crit} requieren atencion urgente", "#d94862")
    return ("Sin alertas criticas", "#1f9d6b")

def panel_prioritario():
    """Construye la lista de elementos que requieren atencion prioritaria."""
    items = []
    # 1. Equipos inoperativos (lo mas urgente)
    estados = calculos.estado_equipos(equipos)
    inoperativos = estados[estados["estado"]=="Inoperativo"]
    for _, eq in inoperativos.iterrows():
        items.append({
            "nivel": "Inoperativo",
            "color": "#d94862",
            "equipo": eq["codigo"],
            "nombre": eq["nombre"],
            "detalle": "Equipo fuera de servicio"
        })
    # 2. Alertas criticas (sin duplicar inoperativos ya listados)
    cods_listados = set(inoperativos["codigo"].tolist())
    criticas = [a for a in lista_alertas if a["nivel"]=="CRITICA"]
    for a in criticas:
        if a["equipo"] in cods_listados:
            continue
        cods_listados.add(a["equipo"])
        items.append({
            "nivel": "Critica",
            "color": "#dd9324",
            "equipo": a["equipo"],
            "nombre": a["nombre"],
            "detalle": a["tipo"]
        })
        if len(items) >= 6:
            break

    if not items:
        return html.Div("No hay situaciones que requieran atencion prioritaria en este momento.",
                        style={"fontSize":"13px","color":"#1f9d6b","padding":"12px 0","textAlign":"center"})

    filas = []
    for it in items[:6]:
        filas.append(html.Div(children=[
            html.Div(children=[
                html.Span(it["nivel"], style={"backgroundColor":it["color"],"color":"white","padding":"2px 9px",
                          "borderRadius":"20px","fontSize":"9.5px","fontWeight":"700"}),
                html.Span(f"  {it['equipo']} - {it['nombre'][:24]}", style={"fontSize":"12.5px","fontWeight":"600","color":"#0b2238","marginLeft":"6px"})
            ], style={"flex":"1"}),
            html.Span(it["detalle"][:30], style={"fontSize":"11px","color":"#8499b1"})
        ], style={"display":"flex","justifyContent":"space-between","alignItems":"center",
                  "padding":"10px 12px","borderBottom":"1px solid #eef2f7","borderLeft":f"3px solid {it['color']}",
                  "backgroundColor":"#fbfdfe","borderRadius":"6px","marginBottom":"6px"}))
    return html.Div(filas)

def contenido_inicio(usuario_actual=None):
    n_alto = (criticidad["nivel"]=="ALTO").sum()
    n_alertas = len(lista_alertas)
    n_riesgo = (prediccion_df["nivel_riesgo"]=="ALTO").sum()

    # Saludo personalizado segun el usuario conectado
    if usuario_actual and usuario_actual in USUARIOS:
        datos = USUARIOS[usuario_actual]
        nombre = datos["nombre"]
        rol = datos["rol"]
        saludo_titulo = f"Bienvenido, {nombre}"
        saludo_sub = f"Has ingresado como {rol}. Este es el resumen del estado actual del parque biomedico del INCOR - EsSalud."
        color_rol = COLOR_ROL.get(rol, "#13b0a5")
    else:
        saludo_titulo = "Bienvenido al Sistema BioCare Dashboard"
        saludo_sub = "Monitoreo predictivo y gestion de criticidad para los equipos biomedicos del INCOR - EsSalud."
        rol = None
        color_rol = "#13b0a5"

    # Construir el contenido del banner
    banner_hijos = [
        html.H2(saludo_titulo, style={"color":"white","fontWeight":"700","fontSize":"26px","marginBottom":"6px"}),
        html.P(saludo_sub, style={"color":"#cfe6ec","fontSize":"14px"})
    ]

    return html.Div(children=[
        # Banner de bienvenida
        html.Div(children=[
            html.Div(children=banner_hijos)
        ], style={"background":"linear-gradient(120deg, #08374d, #13b0a5)","borderRadius":"16px","padding":"32px 36px","marginBottom":"24px"}),

        # Tarjetas de resumen rapido con mini-tendencia
        html.Div(children=[
            tarjeta_inicio("📊","Disponibilidad del parque", f"{disponibilidad:.1f}%","Equipos operativos","#1f9d6b", _tendencia_disponibilidad()),
            tarjeta_inicio("🎯","Equipos criticidad alta", f"{n_alto}","Requieren prioridad","#d94862", ("De 30 equipos totales","#8499b1")),
            tarjeta_inicio("📬","Alertas activas", f"{n_alertas}","Generadas automaticamente","#dd9324", _tendencia_alertas()),
            tarjeta_inicio("🔮","Equipos en riesgo", f"{n_riesgo}","Prediccion de falla","#6c5ce0", ("Riesgo alto de falla","#8499b1")),
        ], style={"display":"flex","gap":"14px","marginBottom":"24px","flexWrap":"wrap"}),

        # Panel de atencion prioritaria + estado del parque
        html.Div(children=[
            # Atencion prioritaria
            html.Div(children=[
                html.Div(children=[
                    html.Span("⚠️  Atencion prioritaria", style={"fontSize":"15px","fontWeight":"700","color":"white"}),
                    html.Div("Lo mas urgente que requiere accion inmediata",
                             style={"fontSize":"11.5px","color":"rgba(255,255,255,0.85)","marginTop":"2px"})
                ], style={"background":"linear-gradient(120deg, #08374d, #d94862)","padding":"14px 18px"}),
                html.Div(panel_prioritario(), style={"padding":"16px"})
            ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","flex":"1.4","overflow":"hidden"}),
            # Mini-grafico de estado del parque
            html.Div(children=[
                html.Div("Estado del parque tecnologico", style={"fontSize":"14px","fontWeight":"700","color":"#08374d",
                         "padding":"16px 18px","borderBottom":"1px solid #e0e7f0"}),
                html.Div(dcc.Graph(figure=graficos.grafico_estado(equipos), config={"displayModeBar":False}), style={"padding":"8px"})
            ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","flex":"1","overflow":"hidden"}),
        ], style={"display":"flex","gap":"16px","marginBottom":"24px","alignItems":"flex-start"}),

        # Accesos rapidos
        html.Div(children=[
            html.Div("Accesos rapidos", style={"fontSize":"15px","fontWeight":"700","color":"#08374d","marginBottom":"14px"}),
            html.Div(children=[
                acceso_rapido("📊","Ver KPIs estrategicos","nav-kpis"),
                acceso_rapido("🎯","Matriz de criticidad","nav-crit"),
                acceso_rapido("📬","Revisar alertas","nav-alertas"),
                acceso_rapido("🔮","Prediccion de fallas","nav-pred"),
            ], style={"display":"flex","gap":"14px","flexWrap":"wrap"})
        ], style={"backgroundColor":"white","borderRadius":"14px","padding":"24px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","marginBottom":"24px"}),

        # Resumen de actividad reciente
        html.Div(children=[
            html.Div("Actividad reciente", style={"fontSize":"15px","fontWeight":"700","color":"#08374d","padding":"18px 22px","borderBottom":"1px solid #e0e7f0"}),
            html.Div(actividad_reciente(), style={"padding":"10px 18px 16px"})
        ], style={"backgroundColor":"white","borderRadius":"14px","boxShadow":"0 4px 16px rgba(8,55,77,0.08)","marginBottom":"24px","overflow":"hidden"}),

        # Pie institucional
        html.Div(children=[
            html.Div(children=[
                html.Div("BioCare Dashboard", style={"fontSize":"14px","fontWeight":"700","color":"#08374d"}),
                html.Div("Sistema de Monitoreo Predictivo y Gestion de Criticidad para el Mantenimiento de Equipos Biomedicos",
                         style={"fontSize":"11.5px","color":"#8499b1","marginTop":"3px"})
            ], style={"flex":"1"}),
            html.Div(children=[
                html.Div("Bioingenieros SAC", style={"fontSize":"12px","fontWeight":"600","color":"#3f5874","textAlign":"right"}),
                html.Div("INCOR - Instituto Nacional Cardiovascular - EsSalud", style={"fontSize":"11px","color":"#8499b1","textAlign":"right","marginTop":"2px"}),
                html.Div("Proyecto Preprofesional - UTEC - Bioingenieria", style={"fontSize":"11px","color":"#8499b1","textAlign":"right","marginTop":"2px"})
            ])
        ], style={"display":"flex","justifyContent":"space-between","alignItems":"center",
                  "backgroundColor":"#f7fafc","border":"1px solid #e0e7f0","borderRadius":"14px","padding":"18px 24px"})
    ])

def actividad_reciente():
    """Construye la lista de las ultimas intervenciones registradas."""
    import pandas as pd
    h = historial.copy()
    h["fecha"] = pd.to_datetime(h["fecha"])
    ultimas = h.sort_values("fecha", ascending=False).head(6)
    ultimas = ultimas.merge(equipos[["codigo","nombre"]], left_on="codigo_equipo", right_on="codigo")
    filas = []
    for _, r in ultimas.iterrows():
        color = "#d94862" if r["tipo_mantenimiento"]=="Correctivo" else "#1f9d6b"
        icono = "🔧" if r["tipo_mantenimiento"]=="Correctivo" else "🗓️"
        filas.append(html.Div(children=[
            html.Span(icono, style={"fontSize":"15px","marginRight":"12px"}),
            html.Div(children=[
                html.Div(children=[
                    html.Span(f"{r['codigo_equipo']} - {r['nombre'][:26]}", style={"fontSize":"12.5px","fontWeight":"600","color":"#0b2238"}),
                    html.Span(r["tipo_mantenimiento"], style={"backgroundColor":color,"color":"white","padding":"1px 8px",
                              "borderRadius":"12px","fontSize":"9.5px","fontWeight":"700","marginLeft":"8px"})
                ]),
                html.Div(r["descripcion"], style={"fontSize":"11px","color":"#8499b1","marginTop":"2px"})
            ], style={"flex":"1"}),
            html.Span(r["fecha"].strftime("%d/%m/%Y"), style={"fontSize":"11px","color":"#8499b1","fontFamily":"monospace","whiteSpace":"nowrap"})
        ], style={"display":"flex","alignItems":"center","padding":"11px 8px","borderBottom":"1px solid #eef2f7"}))
    return html.Div(filas)

def acceso_rapido(icono, texto, id_destino):
    return html.Div(children=[
        html.Div(icono, style={"fontSize":"26px","marginBottom":"8px"}),
        html.Div(texto, style={"fontSize":"13px","fontWeight":"600","color":"#08374d"})
    ], className="acceso-hover", style={"flex":"1","minWidth":"180px","backgroundColor":"#f7fafc","border":"1px solid #e0e7f0",
              "borderRadius":"12px","padding":"20px","textAlign":"center"})

# --- 7. App con barra lateral ---
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "BioCare Dashboard"
# Servidor Flask interno, necesario para el despliegue en produccion (gunicorn en Render)
server = app.server

# Items del menu lateral: (id, icono, etiqueta)
MENU_ITEMS = [
    ("menu-inicio", "\U0001F3E0", "Inicio"),
    ("menu-kpis", "\U0001F4CA", "KPIs Estrategicos"),
    ("menu-crit", "\U0001F3AF", "Criticidad"),
    ("menu-alertas", "\U0001F4EC", "Alertas"),
    ("menu-pred", "\U0001F52E", "Prediccion"),
    ("menu-auto", "\u2699\uFE0F", "Automatizacion"),
]

# Relacion entre el id del menu y la clave de modulo permitida por rol
MENU_A_MODULO = {
    "menu-inicio": "inicio",
    "menu-kpis": "kpis",
    "menu-crit": "crit",
    "menu-alertas": "alertas",
    "menu-pred": "pred",
    "menu-auto": "auto",
}

def item_menu(id_item, icono, etiqueta, activo=False, visible=True):
    estilo = estilo_item_menu(activo)
    if not visible:
        # Si el rol no tiene permiso, ocultamos el item (pero el id sigue existiendo
        # para que los callbacks no fallen)
        estilo = {**estilo, "display":"none"}
    return html.Div(children=[
        html.Span(icono, style={"fontSize":"18px","marginRight":"12px"}),
        html.Span(etiqueta, style={"fontSize":"13.5px","fontWeight":"600"})
    ], id=id_item, className="menu-item", n_clicks=0, style=estilo)

def construir_menu(usuario_actual, seleccion="menu-inicio"):
    """Construye los items del menu mostrando solo los permitidos por el rol."""
    modulos_permitidos = USUARIOS[usuario_actual]["modulos"]
    items = []
    for mid, ico, lab in MENU_ITEMS:
        modulo = MENU_A_MODULO[mid]
        visible = modulo in modulos_permitidos
        items.append(item_menu(mid, ico, lab, activo=(mid==seleccion), visible=visible))
    return items

def estilo_item_menu(activo):
    return {
        "display":"flex","alignItems":"center","padding":"13px 22px","cursor":"pointer",
        "color":"white" if activo else "#9db8c9",
        "backgroundColor":"rgba(255,255,255,0.12)" if activo else "transparent",
        "borderLeft":"4px solid #13b0a5" if activo else "4px solid transparent",
        "transition":"all 0.2s"
    }

# Barra lateral
def construir_sidebar(usuario_actual):
    return html.Div(children=[
        # Logo
        html.Div(children=[
            html.Div("🫀", style={"fontSize":"26px","marginBottom":"6px"}),
            html.Div("BioCare", style={"fontSize":"19px","fontWeight":"800","color":"white","letterSpacing":"-0.5px"}),
            html.Div("Dashboard", style={"fontSize":"12px","color":"#13b0a5","fontWeight":"600","letterSpacing":"2px"})
        ], style={"padding":"26px 22px","borderBottom":"1px solid rgba(255,255,255,0.1)","marginBottom":"10px"}),
        # Items del menu (filtrados por rol)
        html.Div(id="menu-container", children=construir_menu(usuario_actual)),
        # Pie de la barra lateral
        html.Div(children=[
            html.Div("Bioingenieros SAC", style={"fontSize":"11px","color":"#9db8c9","fontWeight":"600"}),
            html.Div("INCOR - EsSalud", style={"fontSize":"10px","color":"#6b8499"})
        ], style={"position":"absolute","bottom":"0","padding":"20px 22px","borderTop":"1px solid rgba(255,255,255,0.1)","width":"100%"})
    ], style={
        "width":"230px","minWidth":"230px","background":"linear-gradient(180deg, #08374d, #0a2a3d)",
        "minHeight":"100vh","position":"relative"
    })

# Barra superior de la zona de contenido
def topbar_con_usuario(titulo, datos_usuario):
    return html.Div(children=[
        html.Div(titulo, id="titulo-seccion", style={"fontSize":"15px","fontWeight":"700","color":"#08374d"}),
        html.Div(children=[
            # Indicador en linea
            html.Div(children=[
                html.Span("\u25CF", style={"color":"#1f9d6b","fontSize":"11px","marginRight":"6px","lineHeight":"1"}),
                html.Span("Sistema en linea", style={"fontSize":"12px","color":"#1f9d6b","fontWeight":"600","lineHeight":"1"})
            ], style={"backgroundColor":"#e4f7ef","padding":"6px 13px","borderRadius":"20px","marginRight":"16px",
                      "display":"inline-flex","alignItems":"center"}),
            # Reloj
            html.Div(children=[
                html.Span("\U0001F550 ", style={"fontSize":"13px"}),
                html.Span(id="reloj-vivo", style={"fontSize":"12.5px","color":"#3f5874","fontWeight":"600","fontFamily":"monospace"})
            ], style={"marginRight":"18px"}),
            # Usuario conectado
            html.Div(children=[
                html.Div(children=[
                    html.Span(datos_usuario["nombre"], style={"fontSize":"12.5px","fontWeight":"700","color":"#08374d"}),
                    html.Span(datos_usuario["rol"], style={"fontSize":"10.5px","color":"white","backgroundColor":COLOR_ROL.get(datos_usuario["rol"],"#0d5c7d"),
                              "padding":"3px 10px","borderRadius":"12px","marginLeft":"8px","fontWeight":"600",
                              "display":"inline-flex","alignItems":"center","lineHeight":"1","verticalAlign":"middle"})
                ], style={"display":"flex","alignItems":"center","justifyContent":"flex-end"})
            ], style={"marginRight":"16px","textAlign":"right"}),
            # Boton cerrar sesion
            html.Button("Cerrar sesion", id="btn-logout", n_clicks=0, className="boton-hover",
                        style={"backgroundColor":"#fdebef","color":"#d94862","border":"none","borderRadius":"8px",
                               "padding":"8px 14px","fontSize":"12px","fontWeight":"700","cursor":"pointer"})
        ], style={"display":"flex","alignItems":"center"})
    ], style={"display":"flex","justifyContent":"space-between","alignItems":"center",
              "padding":"12px 32px","backgroundColor":"white","borderBottom":"1px solid #e0e7f0"})

def topbar(titulo):
    return html.Div(children=[
        # Izquierda: titulo de la seccion
        html.Div(titulo, id="titulo-seccion", style={"fontSize":"15px","fontWeight":"700","color":"#08374d"}),
        # Derecha: reloj en vivo + indicador en linea
        html.Div(children=[
            # Indicador "Sistema en linea"
            html.Div(children=[
                html.Span("●", style={"color":"#1f9d6b","fontSize":"11px","marginRight":"6px","lineHeight":"1"}),
                html.Span("Sistema en linea", style={"fontSize":"12px","color":"#1f9d6b","fontWeight":"600","lineHeight":"1"})
            ], style={"backgroundColor":"#e4f7ef","padding":"6px 13px","borderRadius":"20px","marginRight":"16px",
                      "display":"inline-flex","alignItems":"center"}),
            # Reloj en vivo (se actualiza con el callback)
            html.Div(children=[
                html.Span("🕐 ", style={"fontSize":"13px"}),
                html.Span(id="reloj-vivo", style={"fontSize":"12.5px","color":"#3f5874","fontWeight":"600","fontFamily":"monospace"})
            ])
        ], style={"display":"flex","alignItems":"center"})
    ], style={"display":"flex","justifyContent":"space-between","alignItems":"center",
              "padding":"14px 32px","backgroundColor":"white","borderBottom":"1px solid #e0e7f0"})

# ============================================================
#  PANTALLA DE LOGIN
# ============================================================
def pantalla_login(mensaje_error=""):
    return html.Div(children=[
        html.Div(children=[
            # Logo y titulo
            html.Div("\U0001FAC0", style={"fontSize":"48px","textAlign":"center","marginBottom":"10px"}),
            html.Div("BioCare Dashboard", style={"fontSize":"26px","fontWeight":"800","color":"#08374d","textAlign":"center","letterSpacing":"-0.5px"}),
            html.Div("Sistema de Monitoreo Predictivo - Bioingenieros SAC", style={"fontSize":"12.5px","color":"#8499b1","textAlign":"center","marginBottom":"28px"}),
            # Campo usuario
            html.Div("Usuario", style={"fontSize":"12.5px","fontWeight":"600","color":"#3f5874","marginBottom":"6px"}),
            dcc.Input(id="login-usuario", type="text", placeholder="Escribe tu usuario",
                      className="login-input",
                      style={"width":"100%","height":"46px","padding":"0 14px","borderRadius":"10px",
                             "border":"1.5px solid #e0e7f0","fontSize":"14px","marginBottom":"16px",
                             "boxSizing":"border-box","color":"#08374d"}),
            # Campo contrasena
            html.Div("Contrasena", style={"fontSize":"12.5px","fontWeight":"600","color":"#3f5874","marginBottom":"6px"}),
            dcc.Input(id="login-password", type="password", placeholder="Escribe tu contrasena",
                      className="login-input",
                      style={"width":"100%","height":"46px","padding":"0 14px","borderRadius":"10px",
                             "border":"1.5px solid #e0e7f0","fontSize":"14px","marginBottom":"20px",
                             "boxSizing":"border-box","color":"#08374d"}),
            # Boton ingresar
            html.Button("Iniciar sesion", id="btn-login", n_clicks=0, className="boton-hover",
                        style={"width":"100%","height":"46px","backgroundColor":"#0d5c7d","color":"white",
                               "border":"none","borderRadius":"10px","fontSize":"14.5px","fontWeight":"700",
                               "cursor":"pointer","marginBottom":"14px"}),
            # Mensaje de error
            html.Div(mensaje_error, id="login-error", style={"color":"#d94862","fontSize":"12.5px",
                     "textAlign":"center","minHeight":"18px","fontWeight":"600"}),
            # Ayuda de credenciales (para el jurado)
            html.Div(children=[
                html.Div("Credenciales de acceso para demostracion:", style={"fontSize":"11px","fontWeight":"700","color":"#8499b1","marginBottom":"8px","textTransform":"uppercase","letterSpacing":"0.5px"}),
                html.Div("Supervisor:  admin  /  admin2026", style={"fontSize":"11.5px","color":"#3f5874","marginBottom":"3px","fontFamily":"monospace"}),
                html.Div("Tecnico:  tecnico  /  tecnico2026", style={"fontSize":"11.5px","color":"#3f5874","marginBottom":"3px","fontFamily":"monospace"}),
                html.Div("Jurado:  invitado  /  biocare2026", style={"fontSize":"11.5px","color":"#3f5874","fontFamily":"monospace"}),
            ], style={"marginTop":"20px","padding":"14px 16px","backgroundColor":"#f7fafc","border":"1px solid #e0e7f0","borderRadius":"10px"})
        ], style={"backgroundColor":"white","borderRadius":"18px","padding":"40px","width":"400px",
                  "boxShadow":"0 20px 60px rgba(8,55,77,0.18)"})
    ], style={"display":"flex","justifyContent":"center","alignItems":"center","minHeight":"100vh",
              "background":"linear-gradient(135deg, #08374d, #0d5c7d 60%, #13b0a5)",
              "fontFamily":"Segoe UI, sans-serif"})

# ============================================================
#  DASHBOARD COMPLETO (se muestra tras iniciar sesion)
# ============================================================
def dashboard_completo(usuario_actual):
    datos = USUARIOS[usuario_actual]
    return html.Div(children=[
        construir_sidebar(usuario_actual),
        html.Div(children=[
            topbar_con_usuario("Inicio", datos),
            html.Div(id="contenido", children=contenido_inicio(usuario_actual),
                     style={"padding":"28px 32px","maxWidth":"1300px"}),
            dcc.Interval(id="intervalo-reloj", interval=1000, n_intervals=0),
            # Contenedor donde aparece la ficha modal del equipo
            html.Div(id="contenedor-modal"),
            # Contenedor para formularios de accion (registrar OTM, cambiar estado, etc.)
            html.Div(id="contenedor-formulario"),
            # Componente de descarga para las acciones de la ficha (historial, ficha PDF)
            dcc.Download(id="descarga-ficha"),
            # Almacen de alertas atendidas
            dcc.Store(id="alertas-atendidas", data=[]),
            # Contenedor para el modal de prediccion
            html.Div(id="contenedor-prediccion")
        ], style={"flex":"1","backgroundColor":"#eef2f7","minHeight":"100vh"})
    ], style={"display":"flex","fontFamily":"Segoe UI, sans-serif"})

# ============================================================
#  LAYOUT PRINCIPAL: decide login o dashboard
# ============================================================
app.layout = html.Div(children=[
    # Almacen de sesion: recuerda quien esta conectado
    dcc.Store(id="sesion", storage_type="session"),
    html.Div(id="vista-principal", children=pantalla_login())
])

# --- CALLBACK: actualizar el reloj en vivo cada segundo ---
@app.callback(
    Output("reloj-vivo","children"),
    Input("intervalo-reloj","n_intervals"),
    prevent_initial_call=True
)
def actualizar_reloj(n):
    return _texto_reloj()

def _texto_reloj():
    from datetime import datetime
    dias = ["Lunes","Martes","Miercoles","Jueves","Viernes","Sabado","Domingo"]
    meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto",
             "septiembre","octubre","noviembre","diciembre"]
    ahora = datetime.now()
    dia_sem = dias[ahora.weekday()]
    fecha = f"{dia_sem} {ahora.day} de {meses[ahora.month-1]} {ahora.year}"
    hora = ahora.strftime("%H:%M:%S")
    return f"{fecha}  |  {hora}"

# --- 8. CALLBACK: navegacion de la barra lateral ---
@app.callback(
    [Output("contenido","children"), Output("titulo-seccion","children"),
     Output("menu-container","children")],
    [Input(mid, "n_clicks") for mid, _, _ in MENU_ITEMS],
    dash.dependencies.State("sesion","data")
)
def navegar(*args):
    clicks = args[:-1]
    sesion = args[-1]
    # Si no hay sesion activa, no hacemos nada
    if not sesion or "usuario" not in sesion:
        raise dash.exceptions.PreventUpdate
    usuario_actual = sesion["usuario"]
    modulos_permitidos = USUARIOS[usuario_actual]["modulos"]

    ctx = dash.callback_context
    seleccion = "menu-inicio"
    if ctx.triggered:
        seleccion = ctx.triggered[0]["prop_id"].split(".")[0]

    # Mapa de cada item a su contenido y titulo
    mapa = {
        "menu-inicio": (contenido_inicio, "Inicio"),
        "menu-kpis": (contenido_modulo1, "KPIs Estrategicos"),
        "menu-crit": (contenido_modulo2, "Matriz de Criticidad"),
        "menu-alertas": (contenido_modulo3, "Sistema de Alertas"),
        "menu-pred": (contenido_modulo4, "Modelo Predictivo"),
        "menu-auto": (contenido_modulo5, "Automatizacion de Mantenimientos"),
    }

    # Control de acceso: si el modulo no esta permitido para el rol,
    # redirigimos al inicio (seguridad real, no solo visual)
    modulo_sel = MENU_A_MODULO.get(seleccion, "inicio")
    if modulo_sel not in modulos_permitidos:
        seleccion = "menu-inicio"

    func, titulo = mapa.get(seleccion, (contenido_inicio, "Inicio"))
    nuevo_menu = construir_menu(usuario_actual, seleccion)
    # El inicio recibe el usuario para personalizar el saludo
    if seleccion == "menu-inicio":
        contenido = contenido_inicio(usuario_actual)
    else:
        contenido = func()
    return contenido, titulo, nuevo_menu

# Callback: clasificar falla con el modelo ML
@app.callback(
    Output("resultado-clasificacion","children"),
    Input("btn-clasificar","n_clicks"),
    dash.dependencies.State("input-falla","value")
)
def clasificar(n, texto):
    if not n or not texto:
        return ""
    cat, probs = automatizacion.clasificar_falla(modelo_clf, texto)
    barras = []
    for c, p in probs:
        barras.append(html.Div(children=[
            html.Span(c, style={"width":"90px","display":"inline-block","fontSize":"12px","color":"white"}),
            html.Div(style={"flex":"1","height":"8px","backgroundColor":"rgba(255,255,255,0.2)","borderRadius":"5px","display":"inline-block","verticalAlign":"middle","margin":"0 8px","position":"relative",
                            "width":f"{p}%","maxWidth":"60%"}),
            html.Span(f"{p}%", style={"fontSize":"12px","color":"white","fontFamily":"monospace"})
        ], style={"marginBottom":"6px"}))
    return html.Div(children=[
        html.Div(children=[
            html.Span("Categoria detectada: ", style={"color":"#cfe6ec","fontSize":"13px"}),
            html.Span(cat, style={"color":"white","fontSize":"20px","fontWeight":"800"}),
            html.Span(f"  ({probs[0][1]}% confianza)", style={"color":"#b8e6d3","fontSize":"13px","marginLeft":"8px"})
        ], style={"marginBottom":"14px"}),
    ] + barras + [
        # Orden de trabajo sugerida
        html.Div(children=[
            html.Div("📋 Orden de trabajo sugerida", style={"fontSize":"12.5px","fontWeight":"700","color":"white","marginBottom":"8px"}),
            html.Div(children=[
                html.Div([html.Span("Tipo de mantenimiento: ", style={"color":"#cfe6ec"}), html.Span("Correctivo", style={"color":"white","fontWeight":"600"})], style={"fontSize":"12px","marginBottom":"4px"}),
                html.Div([html.Span("Categoria asignada: ", style={"color":"#cfe6ec"}), html.Span(cat, style={"color":"white","fontWeight":"600"})], style={"fontSize":"12px","marginBottom":"4px"}),
                html.Div([html.Span("Especialidad requerida: ", style={"color":"#cfe6ec"}), html.Span(_especialidad_por_categoria(cat), style={"color":"white","fontWeight":"600"})], style={"fontSize":"12px","marginBottom":"4px"}),
                html.Div([html.Span("Prioridad: ", style={"color":"#cfe6ec"}), html.Span(_prioridad_por_confianza(probs[0][1]), style={"color":"white","fontWeight":"600"})], style={"fontSize":"12px"}),
            ])
        ], style={"backgroundColor":"rgba(255,255,255,0.15)","borderRadius":"10px","padding":"14px","marginTop":"14px"}),

        # Registrar OTM directamente desde el clasificador
        html.Div(children=[
            html.Div("Registrar esta falla como orden de trabajo", style={"fontSize":"12px","fontWeight":"700","color":"white","marginBottom":"8px"}),
            html.Div(children=[
                dcc.Dropdown(id="otm-equipo-clasif",
                    options=[{"label":f"{c} - {equipos[equipos['codigo']==c]['nombre'].values[0]}","value":c} for c in equipos["codigo"].tolist()],
                    placeholder="Selecciona el equipo afectado",
                    style={"flex":"1","fontSize":"12px"}),
                html.Button("Registrar OTM", id="btn-registrar-otm-clasif", n_clicks=0,
                            style={"backgroundColor":"white","color":"#0d5c7d","border":"none","borderRadius":"8px",
                                   "padding":"0 18px","height":"38px","fontSize":"12px","fontWeight":"700","cursor":"pointer","marginLeft":"10px","whiteSpace":"nowrap"})
            ], style={"display":"flex","alignItems":"center"}),
            # Guardar la categoria y descripcion detectadas para el registro
            dcc.Store(id="otm-categoria-clasif", data=cat),
            dcc.Store(id="otm-descripcion-clasif", data=texto),
            html.Div(id="otm-resultado-clasif", style={"marginTop":"10px","fontSize":"12px"})
        ], style={"backgroundColor":"rgba(255,255,255,0.15)","borderRadius":"10px","padding":"14px","marginTop":"12px"})
    ], style={"backgroundColor":"rgba(255,255,255,0.12)","borderRadius":"12px","padding":"16px"})

def _especialidad_por_categoria(cat):
    """Sugiere la especialidad tecnica segun la categoria de falla."""
    mapa = {
        "Electrica":"Tecnico electronico / electricista biomedico",
        "Mecanica":"Tecnico mecanico biomedico",
        "Sensores":"Ingeniero biomedico / metrologia",
        "Software":"Soporte tecnico / informatica biomedica",
        "Calibracion":"Metrologia / laboratorio de calibracion",
        "Desgaste":"Tecnico biomedico (cambio de repuestos)",
    }
    return mapa.get(cat, "Tecnico biomedico general")

def _prioridad_por_confianza(conf):
    """Sugiere la prioridad segun la confianza de la clasificacion."""
    if conf >= 70:
        return "Alta (clasificacion confiable)"
    elif conf >= 45:
        return "Media (revisar manualmente)"
    else:
        return "Requiere revision de un tecnico"

# Callback: ejemplos rapidos llenan el input de falla
@app.callback(
    Output("input-falla","value"),
    Input({"tipo":"ejemplo-falla","texto":dash.dependencies.ALL},"n_clicks"),
    prevent_initial_call=True
)
def usar_ejemplo_falla(clicks):
    if not clicks or not any(clicks):
        raise dash.exceptions.PreventUpdate
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    import json
    disparador = ctx.triggered[0]["prop_id"].split(".")[0]
    texto = json.loads(disparador)["texto"]
    return texto

# Callback: mostrar historial y resumen de un equipo
@app.callback(
    Output("info-equipo","children"),
    Input("dropdown-equipo","value")
)
def mostrar_info(codigo):
    if not codigo:
        return ""
    resumen = automatizacion.resumen_automatico(equipos, historial, codigo)
    recurrentes = automatizacion.fallas_recurrentes(historial, codigo)
    hist = automatizacion.consultar_historial(historial, codigo).head(10)

    # Resumen automatico destacado (generado en lenguaje natural)
    bloque_resumen = html.Div(children=[
        html.Div(children=[
            html.Span("🤖", style={"fontSize":"18px","marginRight":"8px"}),
            html.Span("Resumen automatico generado", style={"fontSize":"12px","fontWeight":"700","color":"#0d5c7d","textTransform":"uppercase","letterSpacing":"0.5px"})
        ], style={"marginBottom":"8px"}),
        html.Div(resumen, style={"fontSize":"13px","color":"#08374d","lineHeight":"1.7"})
    ], style={"backgroundColor":"#f0f7f9","border":"1px solid #cfe6ec","borderLeft":"4px solid #13b0a5",
              "borderRadius":"10px","padding":"14px 18px","marginBottom":"16px"})

    # Recomendaciones automaticas de mantenimiento
    recomendaciones = automatizacion.recomendaciones_equipo(equipos, historial, codigo)
    bloque_recom = html.Div(children=[
        html.Div(children=[
            html.Span("💡", style={"fontSize":"18px","marginRight":"8px"}),
            html.Span("Recomendaciones automaticas", style={"fontSize":"12px","fontWeight":"700","color":"#6c5ce0","textTransform":"uppercase","letterSpacing":"0.5px"})
        ], style={"marginBottom":"8px"}),
        html.Ul(children=[
            html.Li(rec, style={"fontSize":"12.5px","color":"#08374d","lineHeight":"1.6","marginBottom":"5px"})
            for rec in recomendaciones
        ], style={"margin":"0","paddingLeft":"20px"})
    ], style={"backgroundColor":"#f3f0ff","border":"1px solid #d9d0f5","borderLeft":"4px solid #6c5ce0",
              "borderRadius":"10px","padding":"14px 18px","marginBottom":"16px"})

    # Tabla de ultimas intervenciones
    filas_hist = []
    for _, r in hist.iterrows():
        color = "#d94862" if r["tipo_mantenimiento"]=="Correctivo" else "#1f9d6b"
        filas_hist.append(html.Tr(children=[
            html.Td(r["fecha"].strftime("%d/%m/%Y"), style={"padding":"8px 10px","fontSize":"11.5px","color":"#8499b1"}),
            html.Td(r["tipo_mantenimiento"], style={"padding":"8px 10px","fontSize":"11.5px","color":color,"fontWeight":"600"}),
            html.Td(r["descripcion"], style={"padding":"8px 10px","fontSize":"11.5px","color":"#3f5874"})
        ], style={"borderBottom":"1px solid #eef2f7"}))

    return html.Div(children=[
        bloque_resumen,
        bloque_recom,
        html.Div(children=[
            # Grafico de fallas recurrentes
            html.Div(children=[
                html.Div("Fallas recurrentes detectadas", style={"fontSize":"13px","fontWeight":"700","color":"#08374d","marginBottom":"6px"}),
                html.Div("Distribucion de las fallas correctivas por categoria", style={"fontSize":"11px","color":"#8499b1","marginBottom":"6px"}),
                dcc.Graph(figure=graficos.grafico_fallas_recurrentes(recurrentes), config={"displayModeBar":False})
            ], style={"flex":"1","backgroundColor":"#fbfdfe","borderRadius":"10px","padding":"16px","border":"1px solid #e0e7f0"}),
            # Tabla de ultimas intervenciones
            html.Div(children=[
                html.Div("Ultimas 10 intervenciones", style={"fontSize":"13px","fontWeight":"700","color":"#08374d","marginBottom":"12px"}),
                html.Table(children=[html.Tbody(filas_hist)], style={"width":"100%","borderCollapse":"collapse"})
            ], style={"flex":"1.4","backgroundColor":"#fbfdfe","borderRadius":"10px","padding":"16px","border":"1px solid #e0e7f0"})
        ], style={"display":"flex","gap":"14px","alignItems":"flex-start"})
    ])



# ============================================================
#  CALLBACKS DE INICIO Y CIERRE DE SESION
# ============================================================
# Callback de login: verifica credenciales al hacer clic en "Iniciar sesion"
@app.callback(
    [Output("sesion","data"), Output("vista-principal","children")],
    Input("btn-login","n_clicks"),
    [dash.dependencies.State("login-usuario","value"),
     dash.dependencies.State("login-password","value")],
    prevent_initial_call=True
)
def iniciar_sesion(n, usuario, password):
    if not usuario or not password:
        return None, pantalla_login("Por favor completa usuario y contrasena.")
    usuario = usuario.strip().lower()
    if usuario in USUARIOS and USUARIOS[usuario]["password"] == password:
        # Credenciales correctas: guardar sesion y mostrar dashboard
        return {"usuario": usuario}, dashboard_completo(usuario)
    # Credenciales incorrectas
    return None, pantalla_login("Usuario o contrasena incorrectos. Intenta de nuevo.")

# Callback de logout: cierra sesion y vuelve al login
@app.callback(
    [Output("sesion","data", allow_duplicate=True),
     Output("vista-principal","children", allow_duplicate=True)],
    Input("btn-logout","n_clicks"),
    prevent_initial_call=True
)
def cerrar_sesion(n):
    if n and n > 0:
        return None, pantalla_login()
    raise dash.exceptions.PreventUpdate

# ============================================================
#  CALLBACKS: abrir y cerrar la ficha detallada del equipo
# ============================================================
# Callback para ABRIR la ficha al hacer clic en una fila
@app.callback(
    Output("contenedor-modal","children"),
    Input({"tipo":"fila-equipo","codigo":dash.dependencies.ALL},"n_clicks"),
    dash.dependencies.State("sesion","data"),
    prevent_initial_call=True
)
def abrir_modal(clicks_filas, sesion):
    # Si ninguna fila tiene clics reales, no hacer nada
    if not clicks_filas or not any(clicks_filas):
        raise dash.exceptions.PreventUpdate
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    disparador = ctx.triggered[0]["prop_id"]
    if "fila-equipo" in disparador:
        import json
        id_str = disparador.split(".")[0]
        codigo = json.loads(id_str)["codigo"]
        # Obtener el rol del usuario conectado
        rol = "Visualizacion"
        if sesion and "usuario" in sesion:
            rol = USUARIOS[sesion["usuario"]]["rol"]
        return ficha_equipo_modal(codigo, rol)
    raise dash.exceptions.PreventUpdate

# Callback para CERRAR la ficha (boton X o fondo oscurecido)
@app.callback(
    Output("contenedor-modal","children", allow_duplicate=True),
    Input({"tipo":"cerrar-modal","origen":dash.dependencies.ALL},"n_clicks"),
    prevent_initial_call=True
)
def cerrar_modal(clicks_cerrar):
    if clicks_cerrar and any(clicks_cerrar):
        return None
    raise dash.exceptions.PreventUpdate

# ============================================================
#  CALLBACK: filtros globales + buscador (trabajan juntos)
# ============================================================
@app.callback(
    [Output("cuerpo-tabla-crit","children"),
     Output("heatmap-crit","children"),
     Output("tarjetas-resumen-crit","children")],
    [Input("buscador-equipos","value"),
     Input("filtro-area","value"),
     Input("filtro-nivel","value")],
    prevent_initial_call=True
)
def filtrar_criticidad(texto, area, nivel):
    # Partimos de todos los equipos y aplicamos los filtros uno por uno
    datos = criticidad.copy()

    # Filtro por area
    if area and area != "todas":
        datos = datos[datos["area"] == area]

    # Filtro por nivel de criticidad
    if nivel and nivel != "todos":
        datos = datos[datos["nivel"] == nivel]

    # Filtro por texto del buscador
    if texto:
        t = texto.strip().lower()
        datos = datos[
            datos["cod"].str.lower().str.contains(t) |
            datos["nombre"].str.lower().str.contains(t) |
            datos["area"].str.lower().str.contains(t)
        ]

    # Construir la tabla
    if len(datos) == 0:
        tabla = [html.Tr(html.Td("No se encontraron equipos con esos criterios.",
                 colSpan=5, style={"padding":"20px","textAlign":"center","color":"#8499b1","fontSize":"13px"}))]
        heatmap = [html.Div("Sin equipos para mostrar.", style={"gridColumn":"1 / -1","textAlign":"center",
                   "color":"#8499b1","fontSize":"12px","padding":"20px"})]
    else:
        tabla = [fila_tabla(r) for _, r in datos.iterrows()]
        heatmap = [celda_heatmap(r) for _, r in datos.iterrows()]

    # Recalcular las tarjetas resumen con los datos filtrados
    n_alto = (datos["nivel"]=="ALTO").sum()
    n_medio = (datos["nivel"]=="MEDIO").sum()
    n_bajo = (datos["nivel"]=="BAJO").sum()
    tarjetas = [
        tarjeta_resumen("ALTO", n_alto, "Criticidad Alta (indice >= 70)", COLOR_NIVEL, BG_NIVEL),
        tarjeta_resumen("MEDIO", n_medio, "Criticidad Media (40-69)", COLOR_NIVEL, BG_NIVEL),
        tarjeta_resumen("BAJO", n_bajo, "Criticidad Baja (< 40)", COLOR_NIVEL, BG_NIVEL),
    ]
    return tabla, heatmap, tarjetas

# ============================================================
#  CALLBACK: descarga de reportes (Excel / PDF)
# ============================================================
def aplicar_filtros_crit(area, nivel):
    """Devuelve la tabla de criticidad aplicando los filtros activos."""
    datos = criticidad.copy()
    if area and area != "todas":
        datos = datos[datos["area"] == area]
    if nivel and nivel != "todos":
        datos = datos[datos["nivel"] == nivel]
    return datos

@app.callback(
    Output("descarga-reporte","data"),
    [Input("btn-excel","n_clicks"), Input("btn-pdf","n_clicks")],
    [dash.dependencies.State("filtro-area","value"),
     dash.dependencies.State("filtro-nivel","value")],
    prevent_initial_call=True
)
def descargar_reporte(clicks_excel, clicks_pdf, area, nivel):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    disparador = ctx.triggered[0]["prop_id"].split(".")[0]

    # Aplicar los filtros activos a los datos
    datos = aplicar_filtros_crit(area, nivel)
    if len(datos) == 0:
        raise dash.exceptions.PreventUpdate

    from io import BytesIO
    from datetime import datetime
    fecha = datetime.now().strftime("%Y%m%d")

    # ---- DESCARGA EXCEL ----
    if disparador == "btn-excel":
        import pandas as pd
        tabla = datos[["cod","nombre","tipo","area","marca","anio","frec_anual","costo_prom","indice","nivel"]].copy()
        tabla.columns = ["Codigo","Equipo","Tipo","Area","Marca","Anio","Fallas/anio","Costo prom (S/)","Indice","Nivel"]
        def to_excel(buffer):
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                tabla.to_excel(writer, index=False, sheet_name="Criticidad")
        return dcc.send_bytes(to_excel, f"BioCare_Criticidad_{fecha}.xlsx")

    # ---- DESCARGA PDF ----
    if disparador == "btn-pdf":
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        def to_pdf(buffer):
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm,
                                    leftMargin=1.5*cm, rightMargin=1.5*cm)
            styles = getSampleStyleSheet()
            elementos = []
            elementos.append(Paragraph("BioCare Dashboard", styles["Title"]))
            elementos.append(Paragraph("Reporte de Matriz de Criticidad - Bioingenieros SAC", styles["Normal"]))
            filtro_txt = []
            if area and area != "todas": filtro_txt.append(f"Area: {area}")
            if nivel and nivel != "todos": filtro_txt.append(f"Nivel: {nivel}")
            if filtro_txt:
                elementos.append(Paragraph("Filtros aplicados: " + " | ".join(filtro_txt), styles["Normal"]))
            elementos.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}  -  Total: {len(datos)} equipos", styles["Normal"]))
            elementos.append(Spacer(1, 14))

            datos_tabla = [["Codigo","Equipo","Area","Indice","Nivel"]]
            for _, r in datos.iterrows():
                datos_tabla.append([r["cod"], r["nombre"][:28], r["area"][:22], str(r["indice"]), r["nivel"]])
            t = Table(datos_tabla, colWidths=[2.2*cm, 6*cm, 5*cm, 2*cm, 2*cm])
            t.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#08374d")),
                ("TEXTCOLOR",(0,0),(-1,0),colors.white),
                ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
                ("FONTSIZE",(0,0),(-1,-1),8.5),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#eef2f7")]),
                ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#b0c8d8")),
                ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
            ]))
            elementos.append(t)
            doc.build(elementos)
        return dcc.send_bytes(to_pdf, f"BioCare_Criticidad_{fecha}.pdf")

    raise dash.exceptions.PreventUpdate

# ============================================================
#  CALLBACKS: registrar nueva OTM
# ============================================================
# Abrir el formulario al pulsar "Registrar OTM"
@app.callback(
    Output("contenedor-formulario","children"),
    Input({"tipo":"accion-ficha","accion":dash.dependencies.ALL,"cod":dash.dependencies.ALL},"n_clicks"),
    prevent_initial_call=True
)
def abrir_formulario_accion(clicks):
    if not clicks or not any(clicks):
        raise dash.exceptions.PreventUpdate
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    import json
    disparador = ctx.triggered[0]["prop_id"].split(".")[0]
    info = json.loads(disparador)
    accion = info["accion"]
    codigo = info["cod"]
    # Por ahora solo "registrar" tiene formulario (las demas acciones vienen en sub-pasos siguientes)
    if accion == "registrar":
        return formulario_registrar_otm(codigo)
    if accion == "estado":
        return formulario_cambiar_estado(codigo)
    if accion == "programar":
        return formulario_programar_mant(codigo)
    raise dash.exceptions.PreventUpdate

# Clasificar la descripcion automaticamente
@app.callback(
    [Output("otm-categoria","value"), Output("otm-clasificacion-info","children")],
    Input("otm-btn-clasificar","n_clicks"),
    dash.dependencies.State("otm-descripcion","value"),
    prevent_initial_call=True
)
def clasificar_otm(n, descripcion):
    if not n or not descripcion:
        raise dash.exceptions.PreventUpdate
    cat, probs = automatizacion.clasificar_falla(modelo_clf, descripcion)
    # Mapear el nombre sin tilde del modelo al nombre con tilde del dropdown
    mapa_tildes = {"Electrica":"Eléctrica","Mecanica":"Mecánica","Sensores":"Sensores",
                   "Software":"Software","Calibracion":"Calibración","Desgaste":"Desgaste"}
    cat_final = mapa_tildes.get(cat, cat)
    confianza = probs[0][1]
    return cat_final, f"🤖 Categoria sugerida: {cat_final} (confianza {confianza}%)"

# Guardar la nueva OTM
@app.callback(
    [Output("otm-mensaje-guardado","children"), Output("otm-mensaje-guardado","style")],
    Input("otm-btn-guardar","n_clicks"),
    [dash.dependencies.State("otm-codigo-actual","data"),
     dash.dependencies.State("otm-tipo","value"),
     dash.dependencies.State("otm-categoria","value"),
     dash.dependencies.State("otm-urgencia","value"),
     dash.dependencies.State("otm-descripcion","value"),
     dash.dependencies.State("otm-costo","value"),
     dash.dependencies.State("otm-tecnico","value"),
     dash.dependencies.State("otm-horas","value"),
     dash.dependencies.State("otm-estado","value")],
    prevent_initial_call=True
)
def guardar_otm(n, codigo, tipo, categoria, urgencia, descripcion, costo, tecnico, horas, estado):
    if not n:
        raise dash.exceptions.PreventUpdate
    estilo_base = {"fontSize":"12.5px","textAlign":"center","marginTop":"10px","fontWeight":"600"}
    # Validar campos minimos
    if not descripcion:
        return "Por favor escribe la descripcion del trabajo.", {**estilo_base,"color":"#d94862"}
    if tipo == "Correctivo" and not categoria:
        return "Por favor selecciona o clasifica la categoria de falla.", {**estilo_base,"color":"#d94862"}
    # Para preventivos, la categoria es "—"
    cat_final = categoria if tipo == "Correctivo" else "—"
    urg_final = urgencia if tipo == "Correctivo" else "Programado"
    try:
        global historial, criticidad, prediccion_df, lista_alertas
        nuevo_id = calculos.agregar_otm(codigo, tipo, cat_final, urg_final, descripcion,
                                        costo if costo else 0, tecnico, horas if horas else 1, estado)
        # Recargar el historial en memoria para que los cambios se reflejen
        _, historial = calculos.cargar_datos()
        return f"✓ Orden {nuevo_id} registrada y guardada correctamente.", {**estilo_base,"color":"#1f9d6b"}
    except Exception as e:
        return f"Error al guardar: {str(e)}", {**estilo_base,"color":"#d94862"}

# Guardar cambio de estado operativo
@app.callback(
    [Output("estado-mensaje","children"), Output("estado-mensaje","style")],
    Input("estado-btn-guardar","n_clicks"),
    [dash.dependencies.State("estado-codigo-actual","data"),
     dash.dependencies.State("estado-nuevo","value")],
    prevent_initial_call=True
)
def guardar_estado(n, codigo, nuevo_estado):
    if not n:
        raise dash.exceptions.PreventUpdate
    estilo_base = {"fontSize":"12.5px","textAlign":"center","marginTop":"10px","fontWeight":"600"}
    try:
        calculos.guardar_estado_equipo(codigo, estado=nuevo_estado)
        return f"✓ Estado actualizado a '{nuevo_estado}' correctamente.", {**estilo_base,"color":"#1f9d6b"}
    except Exception as e:
        return f"Error: {str(e)}", {**estilo_base,"color":"#d94862"}

# Guardar programacion de mantenimiento
@app.callback(
    [Output("prog-mensaje","children"), Output("prog-mensaje","style")],
    Input("prog-btn-guardar","n_clicks"),
    [dash.dependencies.State("prog-codigo-actual","data"),
     dash.dependencies.State("prog-fecha","date")],
    prevent_initial_call=True
)
def guardar_programacion(n, codigo, fecha):
    if not n:
        raise dash.exceptions.PreventUpdate
    estilo_base = {"fontSize":"12.5px","textAlign":"center","marginTop":"10px","fontWeight":"600"}
    if not fecha:
        return "Por favor selecciona una fecha.", {**estilo_base,"color":"#d94862"}
    try:
        calculos.guardar_estado_equipo(codigo, proximo_mant=fecha)
        from datetime import datetime
        fecha_fmt = datetime.strptime(fecha[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
        return f"✓ Proximo mantenimiento programado para el {fecha_fmt}.", {**estilo_base,"color":"#1f9d6b"}
    except Exception as e:
        return f"Error: {str(e)}", {**estilo_base,"color":"#d94862"}

# Cerrar el formulario
@app.callback(
    Output("contenedor-formulario","children", allow_duplicate=True),
    Input({"tipo":"cerrar-form","origen":dash.dependencies.ALL},"n_clicks"),
    prevent_initial_call=True
)
def cerrar_formulario(clicks):
    if clicks and any(clicks):
        return None
    raise dash.exceptions.PreventUpdate

# ============================================================
#  CALLBACK: descargar historial del equipo (Excel) y exportar ficha (PDF)
# ============================================================
@app.callback(
    Output("descarga-ficha","data"),
    Input({"tipo":"accion-ficha","accion":dash.dependencies.ALL,"cod":dash.dependencies.ALL},"n_clicks"),
    prevent_initial_call=True
)
def descargar_desde_ficha(clicks):
    if not clicks or not any(clicks):
        raise dash.exceptions.PreventUpdate
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    import json
    disparador = ctx.triggered[0]["prop_id"].split(".")[0]
    info = json.loads(disparador)
    accion = info["accion"]
    codigo = info["cod"]

    # Solo estas dos acciones generan descargas
    if accion not in ["descargar", "exportar"]:
        raise dash.exceptions.PreventUpdate

    from datetime import datetime
    fecha = datetime.now().strftime("%Y%m%d")
    nombre = equipos[equipos["codigo"]==codigo]["nombre"].values[0]
    h = historial[historial["codigo_equipo"]==codigo].sort_values("fecha", ascending=False)

    # ---- DESCARGAR HISTORIAL EN EXCEL ----
    if accion == "descargar":
        tabla = h[["id_registro","fecha","tipo_mantenimiento","categoria_falla","urgencia",
                   "descripcion","tecnico","horas_intervencion","costo_soles","estado_post"]].copy()
        # Formatear la fecha para mostrar solo dia/mes/ano (sin la hora 00:00:00)
        tabla["fecha"] = pd.to_datetime(tabla["fecha"]).dt.strftime("%d/%m/%Y")
        tabla.columns = ["N. OTM","Fecha","Tipo","Categoria","Urgencia","Descripcion",
                         "Tecnico","Horas","Costo (S/)","Estado final"]
        def to_excel(buffer):
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                tabla.to_excel(writer, index=False, sheet_name="Historial OTM")
        return dcc.send_bytes(to_excel, f"Historial_{codigo}_{fecha}.xlsx")

    # ---- EXPORTAR FICHA TECNICA EN PDF ----
    if accion == "exportar":
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        r = criticidad[criticidad["cod"]==codigo].iloc[0]
        corr = h[h["tipo_mantenimiento"]=="Correctivo"]
        prev = h[h["tipo_mantenimiento"]=="Preventivo"]
        costo_total = h["costo_soles"].sum()
        eq_estado = calculos.estado_equipos(equipos)
        estado = eq_estado[eq_estado["codigo"]==codigo]["estado"].values[0]

        def to_pdf(buffer):
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm,
                                    leftMargin=1.8*cm, rightMargin=1.8*cm)
            styles = getSampleStyleSheet()
            titulo_st = ParagraphStyle("t", parent=styles["Title"], fontSize=17, textColor=colors.HexColor("#08374d"))
            sub_st = ParagraphStyle("s", parent=styles["Normal"], fontSize=10, textColor=colors.HexColor("#3f5874"))
            sec_st = ParagraphStyle("sec", parent=styles["Normal"], fontSize=12, textColor=colors.HexColor("#08374d"),
                                    spaceBefore=12, spaceAfter=6, fontName="Helvetica-Bold")
            elementos = []
            elementos.append(Paragraph("FICHA TECNICA DEL EQUIPO", titulo_st))
            elementos.append(Paragraph("BioCare Dashboard - Bioingenieros SAC | INCOR - EsSalud", sub_st))
            elementos.append(Spacer(1, 12))
            # Datos de identificacion
            elementos.append(Paragraph("1. Datos de identificacion", sec_st))
            datos_id = [
                ["Codigo", r["cod"], "Marca", r["marca"]],
                ["Equipo", r["nombre"][:30], "Tipo", r["tipo"]],
                ["Area / Servicio", r["area"][:22], "Ano", str(r["anio"])],
                ["Antiguedad", f"{r['antiguedad']} anos", "Estado", estado],
                ["Nivel criticidad", r["nivel"], "Indice", str(r["indice"])],
            ]
            t1 = Table(datos_id, colWidths=[3.5*cm, 5*cm, 3*cm, 5*cm])
            t1.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#eef2f7")),
                ("BACKGROUND",(2,0),(2,-1),colors.HexColor("#eef2f7")),
                ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
                ("FONTNAME",(2,0),(2,-1),"Helvetica-Bold"),
                ("FONTSIZE",(0,0),(-1,-1),9),
                ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#cfd9e6")),
                ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
            ]))
            elementos.append(t1)
            # Resumen de mantenimiento
            elementos.append(Paragraph("2. Resumen de mantenimiento", sec_st))
            resumen = [
                ["Total intervenciones", str(len(h)), "Preventivos", str(len(prev))],
                ["Correctivos", str(len(corr)), "Costo acumulado", f"S/ {costo_total:,.0f}"],
            ]
            t2 = Table(resumen, colWidths=[4.25*cm, 4.25*cm, 4.25*cm, 4.25*cm])
            t2.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#eef2f7")),
                ("BACKGROUND",(2,0),(2,-1),colors.HexColor("#eef2f7")),
                ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
                ("FONTNAME",(2,0),(2,-1),"Helvetica-Bold"),
                ("FONTSIZE",(0,0),(-1,-1),9),
                ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#cfd9e6")),
                ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
            ]))
            elementos.append(t2)
            # Historial de OTM (ultimas 15)
            elementos.append(Paragraph("3. Historial de ordenes de trabajo (ultimas 15)", sec_st))
            datos_otm = [["N. OTM","Fecha","Tipo","Descripcion","Costo"]]
            for _, reg in h.head(15).iterrows():
                fecha_r = reg["fecha"].strftime("%d/%m/%Y") if pd.notna(reg["fecha"]) else "-"
                costo_r = f"S/ {reg['costo_soles']:,.0f}" if pd.notna(reg["costo_soles"]) else "-"
                datos_otm.append([reg["id_registro"], fecha_r, reg["tipo_mantenimiento"],
                                  str(reg["descripcion"])[:32], costo_r])
            t3 = Table(datos_otm, colWidths=[2.3*cm, 2.3*cm, 2.5*cm, 7*cm, 2.4*cm])
            t3.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#08374d")),
                ("TEXTCOLOR",(0,0),(-1,0),colors.white),
                ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
                ("FONTSIZE",(0,0),(-1,-1),8),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#eef2f7")]),
                ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#cfd9e6")),
                ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ]))
            elementos.append(t3)
            elementos.append(Spacer(1, 16))
            pie_st = ParagraphStyle("p", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#8499b1"))
            elementos.append(Paragraph(f"Documento generado el {datetime.now().strftime('%d/%m/%Y')} - Datos simulados con respaldo IETSI-EsSalud", pie_st))
            doc.build(elementos)
        return dcc.send_bytes(to_pdf, f"Ficha_{codigo}_{fecha}.pdf")

    raise dash.exceptions.PreventUpdate

# ============================================================
#  CALLBACK: actualizar KPIs segun el anio seleccionado
# ============================================================
@app.callback(
    [Output("contenedor-kpis","children"),
     Output("contenedor-graficos-kpi","children")],
    Input("filtro-anio-kpi","value"),
    prevent_initial_call=True
)
def actualizar_kpis(anio):
    return construir_tarjetas_kpi(anio), construir_graficos_kpi(anio)

# ============================================================
#  CALLBACKS: filtro de alertas y marcar como atendidas
# ============================================================
@app.callback(
    [Output("lista-alertas","children"),
     Output("alertas-atendidas","data")],
    [Input("filtro-nivel-alerta","value"),
     Input("buscador-alertas","value"),
     Input("agrupar-alertas","value"),
     Input({"tipo":"alerta-atender","idx":dash.dependencies.ALL},"n_clicks")],
    dash.dependencies.State("alertas-atendidas","data"),
    prevent_initial_call=True
)
def gestionar_alertas(nivel_filtro, texto_busqueda, agrupar, clicks_atender, atendidas):
    if atendidas is None:
        atendidas = []
    ctx = dash.callback_context

    # Si se hizo clic en un boton de atender, alternar el estado
    if ctx.triggered:
        disparador = ctx.triggered[0]["prop_id"]
        if "alerta-atender" in disparador and ctx.triggered[0]["value"]:
            import json
            id_str = disparador.split(".")[0]
            idx = json.loads(id_str)["idx"]
            if idx in atendidas:
                atendidas = [x for x in atendidas if x != idx]
            else:
                atendidas = atendidas + [idx]

    # Filtrar alertas por nivel y por texto de busqueda
    indices_filtrados = []
    for i, a in enumerate(lista_alertas):
        if nivel_filtro != "todos" and a["nivel"] != nivel_filtro:
            continue
        if texto_busqueda:
            t = texto_busqueda.strip().lower()
            if t not in a["equipo"].lower() and t not in a["nombre"].lower() and t not in a["tipo"].lower():
                continue
        indices_filtrados.append(i)

    if not indices_filtrados:
        return [html.Div("No hay alertas que coincidan con los criterios.",
                style={"textAlign":"center","color":"#8499b1","padding":"30px","fontSize":"13px"})], atendidas

    # Modo agrupado por equipo
    if agrupar and "agrupar" in agrupar:
        from collections import defaultdict
        grupos = defaultdict(list)
        for i in indices_filtrados:
            grupos[lista_alertas[i]["equipo"]].append(i)
        filas = []
        for equipo in sorted(grupos.keys()):
            indices_eq = grupos[equipo]
            nombre_eq = lista_alertas[indices_eq[0]]["nombre"]
            # Encabezado del grupo
            filas.append(html.Div(children=[
                html.Span(f"{equipo} - {nombre_eq}", style={"fontSize":"12.5px","fontWeight":"700","color":"#08374d"}),
                html.Span(f"  ({len(indices_eq)} alerta{'s' if len(indices_eq)>1 else ''})", style={"fontSize":"11px","color":"#8499b1"})
            ], style={"backgroundColor":"#eef2f7","borderRadius":"8px","padding":"8px 14px","marginBottom":"8px","marginTop":"6px"}))
            for i in indices_eq:
                filas.append(fila_alerta(lista_alertas[i], i, atendida=(i in atendidas)))
        return filas, atendidas

    # Modo lista normal
    filas = [fila_alerta(lista_alertas[i], i, atendida=(i in atendidas)) for i in indices_filtrados]
    return filas, atendidas

# Abrir la ficha del equipo desde una alerta
@app.callback(
    Output("contenedor-modal","children", allow_duplicate=True),
    Input({"tipo":"alerta-ficha","cod":dash.dependencies.ALL},"n_clicks"),
    dash.dependencies.State("sesion","data"),
    prevent_initial_call=True
)
def abrir_ficha_desde_alerta(clicks, sesion):
    if not clicks or not any(clicks):
        raise dash.exceptions.PreventUpdate
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    import json
    disparador = ctx.triggered[0]["prop_id"].split(".")[0]
    codigo = json.loads(disparador)["cod"]
    rol = "Visualizacion"
    if sesion and "usuario" in sesion:
        rol = USUARIOS[sesion["usuario"]]["rol"]
    return ficha_equipo_modal(codigo, rol)

# ============================================================
#  CALLBACK: descargar reporte de alertas (Excel / PDF)
# ============================================================
@app.callback(
    Output("descarga-alertas","data"),
    [Input("btn-alertas-excel","n_clicks"), Input("btn-alertas-pdf","n_clicks")],
    prevent_initial_call=True
)
def descargar_alertas(clicks_excel, clicks_pdf):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    disparador = ctx.triggered[0]["prop_id"].split(".")[0]
    if not ctx.triggered[0]["value"]:
        raise dash.exceptions.PreventUpdate

    from datetime import datetime
    fecha = datetime.now().strftime("%Y%m%d")

    # Preparar los datos de alertas
    datos = [{
        "Nivel": a["nivel"], "Equipo": a["equipo"], "Nombre": a["nombre"],
        "Tipo de alerta": a["tipo"], "Detalle": a["detalle"],
        "Antiguedad (dias)": a.get("antiguedad", 0)
    } for a in lista_alertas]

    # ---- EXCEL ----
    if disparador == "btn-alertas-excel":
        tabla = pd.DataFrame(datos)
        def to_excel(buffer):
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                tabla.to_excel(writer, index=False, sheet_name="Alertas")
        return dcc.send_bytes(to_excel, f"Alertas_BioCare_{fecha}.xlsx")

    # ---- PDF ----
    if disparador == "btn-alertas-pdf":
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        def to_pdf(buffer):
            doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=2*cm, bottomMargin=2*cm)
            styles = getSampleStyleSheet()
            elementos = []
            elementos.append(Paragraph("BioCare Dashboard - Reporte de Alertas", styles["Title"]))
            elementos.append(Paragraph(f"Bioingenieros SAC | INCOR - EsSalud  -  {datetime.now().strftime('%d/%m/%Y')}", styles["Normal"]))
            n_crit = sum(1 for a in lista_alertas if a["nivel"]=="CRITICA")
            n_alta = sum(1 for a in lista_alertas if a["nivel"]=="ALTA")
            n_media = sum(1 for a in lista_alertas if a["nivel"]=="MEDIA")
            elementos.append(Paragraph(f"Total: {len(lista_alertas)} alertas ({n_crit} criticas, {n_alta} altas, {n_media} medias)", styles["Normal"]))
            elementos.append(Spacer(1, 14))
            tabla_datos = [["Nivel","Equipo","Nombre","Tipo de alerta","Detalle"]]
            for a in lista_alertas:
                tabla_datos.append([a["nivel"], a["equipo"], a["nombre"][:22], a["tipo"][:26], a["detalle"][:40]])
            t = Table(tabla_datos, colWidths=[2*cm, 2*cm, 4.5*cm, 5*cm, 8*cm])
            t.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#08374d")),
                ("TEXTCOLOR",(0,0),(-1,0),colors.white),
                ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
                ("FONTSIZE",(0,0),(-1,-1),8),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#eef2f7")]),
                ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#cfd9e6")),
                ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ]))
            elementos.append(t)
            doc.build(elementos)
        return dcc.send_bytes(to_pdf, f"Alertas_BioCare_{fecha}.pdf")

    raise dash.exceptions.PreventUpdate

# ============================================================
#  CALLBACKS: modal de detalle de prediccion
# ============================================================
@app.callback(
    Output("contenedor-prediccion","children"),
    Input({"tipo":"fila-prediccion","codigo":dash.dependencies.ALL},"n_clicks"),
    prevent_initial_call=True
)
def abrir_modal_prediccion(clicks):
    if not clicks or not any(clicks):
        raise dash.exceptions.PreventUpdate
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    import json
    disparador = ctx.triggered[0]["prop_id"].split(".")[0]
    codigo = json.loads(disparador)["codigo"]
    return modal_prediccion(codigo)

@app.callback(
    Output("contenedor-prediccion","children", allow_duplicate=True),
    Input({"tipo":"cerrar-pred","origen":dash.dependencies.ALL},"n_clicks"),
    prevent_initial_call=True
)
def cerrar_modal_prediccion(clicks):
    if clicks and any(clicks):
        return None
    raise dash.exceptions.PreventUpdate

# ============================================================
#  CALLBACK: filtro por nivel de riesgo en prediccion
# ============================================================
@app.callback(
    Output("cuerpo-tabla-pred","children"),
    Input("filtro-riesgo-pred","value"),
    prevent_initial_call=True
)
def filtrar_prediccion(nivel):
    if nivel == "todos":
        datos = prediccion_df
    else:
        datos = prediccion_df[prediccion_df["nivel_riesgo"] == nivel]
    if len(datos) == 0:
        return [html.Tr(html.Td("No hay equipos en este nivel de riesgo.",
                colSpan=5, style={"padding":"20px","textAlign":"center","color":"#8499b1","fontSize":"13px"}))]
    return [fila_prediccion(r) for _, r in datos.iterrows()]

# ============================================================
#  CALLBACKS: simulador what-if
# ============================================================
# Al cambiar de equipo, cargar sus valores actuales en los sliders
@app.callback(
    [Output("sim-frec","value"), Output("sim-dias","value"),
     Output("sim-antiguedad","value"), Output("sim-indice","value"),
     Output("sim-costo","data"), Output("sim-prob-actual","data")],
    Input("sim-equipo","value"),
    prevent_initial_call=True
)
def cargar_equipo_simulador(codigo):
    v = prediccion.valores_equipo(prediccion_df, codigo)
    if v is None:
        raise dash.exceptions.PreventUpdate
    return v["frec_fallas"], v["dias_ultima_falla"], v["antiguedad"], v["indice_crit"], v["costo_prom"], v["prob_actual"]

# Al mover los sliders, recalcular la probabilidad
@app.callback(
    [Output("sim-resultado","children"), Output("sim-resultado","style"),
     Output("sim-nivel","children"), Output("sim-nivel","style"),
     Output("sim-comparacion","children")],
    [Input("sim-frec","value"), Input("sim-dias","value"),
     Input("sim-antiguedad","value"), Input("sim-indice","value")],
    [dash.dependencies.State("sim-costo","data"),
     dash.dependencies.State("sim-prob-actual","data")],
    prevent_initial_call=True
)
def simular_prediccion(frec, dias, antiguedad, indice, costo, prob_actual):
    prob, nivel = prediccion.predecir_personalizado(equipos, historial, frec, dias, antiguedad, indice, costo if costo else 400)
    color = COLOR_NIVEL[nivel]
    estilo_resultado = {"fontSize":"44px","fontWeight":"800","color":color,"textAlign":"center","margin":"8px 0"}
    estilo_nivel = {"fontSize":"13px","fontWeight":"700","textAlign":"center","marginBottom":"12px","color":color}
    # Comparacion con el valor actual
    if prob_actual is not None:
        diff = prob - prob_actual
        if abs(diff) < 0.5:
            comp = f"Igual al valor actual ({prob_actual:.1f}%)"
        elif diff < 0:
            comp = f"▼ {abs(diff):.1f}% menos que el actual ({prob_actual:.1f}%)"
        else:
            comp = f"▲ {diff:.1f}% mas que el actual ({prob_actual:.1f}%)"
    else:
        comp = ""
    return f"{prob:.1f}%", estilo_resultado, f"Nivel {nivel}", estilo_nivel, comp

# ============================================================
#  CALLBACKS: comparacion de equipos y descarga de prediccion
# ============================================================
@app.callback(
    Output("comp-resultado","children"),
    [Input("comp-equipo-1","value"), Input("comp-equipo-2","value")],
    prevent_initial_call=True
)
def actualizar_comparacion(cod1, cod2):
    return html.Div(children=[
        tarjeta_comparacion(cod1), tarjeta_comparacion(cod2)
    ], style={"display":"flex","gap":"14px"})

@app.callback(
    Output("descarga-prediccion","data"),
    [Input("btn-pred-excel","n_clicks"), Input("btn-pred-pdf","n_clicks")],
    prevent_initial_call=True
)
def descargar_prediccion(clicks_excel, clicks_pdf):
    ctx = dash.callback_context
    if not ctx.triggered or not ctx.triggered[0]["value"]:
        raise dash.exceptions.PreventUpdate
    disparador = ctx.triggered[0]["prop_id"].split(".")[0]
    from datetime import datetime
    fecha = datetime.now().strftime("%Y%m%d")

    # Preparar datos
    cols = ["cod","nombre","prob_falla","nivel_riesgo","horizonte_dias","frec_fallas","dias_ultima_falla","antiguedad","indice_crit","costo_prom"]
    datos = prediccion_df[cols].copy()
    datos.columns = ["Codigo","Equipo","Prob. falla (%)","Nivel riesgo","Horizonte (dias)","Frec. fallas","Dias sin falla","Antiguedad","Indice crit.","Costo prom."]

    if disparador == "btn-pred-excel":
        def to_excel(buffer):
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                datos.to_excel(writer, index=False, sheet_name="Prediccion")
        return dcc.send_bytes(to_excel, f"Prediccion_BioCare_{fecha}.xlsx")

    if disparador == "btn-pred-pdf":
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        def to_pdf(buffer):
            doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=1.6*cm, bottomMargin=1.6*cm)
            styles = getSampleStyleSheet()
            els = [Paragraph("BioCare Dashboard - Reporte de Prediccion de Fallas", styles["Title"])]
            els.append(Paragraph(f"Bioingenieros SAC | INCOR - EsSalud  -  {datetime.now().strftime('%d/%m/%Y')}", styles["Normal"]))
            metricas = prediccion.evaluar_modelo(equipos, historial)
            els.append(Paragraph(f"Modelo: regresion logistica | Precision: {metricas['accuracy']}% | Validacion cruzada: {metricas['cv']}%", styles["Normal"]))
            els.append(Spacer(1, 12))
            tabla_datos = [["Codigo","Equipo","Prob.","Riesgo","Horiz.","Frec.","Dias","Antig.","Indice"]]
            for _, r in prediccion_df.iterrows():
                tabla_datos.append([r["cod"], r["nombre"][:24], f"{r['prob_falla']:.0f}%", r["nivel_riesgo"],
                                    f"{r['horizonte_dias']}d", f"{r['frec_fallas']:.1f}", str(int(r['dias_ultima_falla'])),
                                    f"{int(r['antiguedad'])}a", str(int(r['indice_crit']))])
            t = Table(tabla_datos, colWidths=[1.8*cm,5.5*cm,1.6*cm,1.8*cm,1.5*cm,1.4*cm,1.3*cm,1.4*cm,1.6*cm])
            t.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#08374d")),
                ("TEXTCOLOR",(0,0),(-1,0),colors.white),
                ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
                ("FONTSIZE",(0,0),(-1,-1),7.5),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#eef2f7")]),
                ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#cfd9e6")),
                ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
            ]))
            els.append(t)
            doc.build(els)
        return dcc.send_bytes(to_pdf, f"Prediccion_BioCare_{fecha}.pdf")
    raise dash.exceptions.PreventUpdate

# ============================================================
#  CALLBACK: clasificacion por lote
# ============================================================
@app.callback(
    Output("resultado-lote","children"),
    Input("btn-lote","n_clicks"),
    dash.dependencies.State("input-lote","value"),
    prevent_initial_call=True
)
def clasificar_lote(n, texto):
    if not n or not texto:
        raise dash.exceptions.PreventUpdate
    # Separar por lineas no vacias
    lineas = [l.strip() for l in texto.split("\n") if l.strip()]
    if not lineas:
        return html.Div("No se ingresaron descripciones validas.", style={"fontSize":"13px","color":"#8499b1"})

    from collections import Counter
    filas = []
    conteo_cat = Counter()
    for i, linea in enumerate(lineas):
        cat, probs = automatizacion.clasificar_falla(modelo_clf, linea)
        conteo_cat[cat] += 1
        color = {"Electrica":"#dd9324","Eléctrica":"#dd9324","Mecanica":"#6c5ce0","Mecánica":"#6c5ce0",
                 "Sensores":"#d94862","Software":"#0d5c7d","Calibracion":"#13b0a5","Calibración":"#13b0a5","Desgaste":"#1f9d6b"}.get(cat, "#8499b1")
        filas.append(html.Tr(children=[
            html.Td(str(i+1), style={"padding":"9px 10px","fontSize":"11px","color":"#8499b1","fontFamily":"monospace"}),
            html.Td(linea[:60], style={"padding":"9px 10px","fontSize":"12px","color":"#3f5874"}),
            html.Td(html.Span(cat, style={"backgroundColor":color,"color":"white","padding":"2px 10px",
                    "borderRadius":"20px","fontSize":"11px","fontWeight":"700"}), style={"padding":"9px 10px"}),
            html.Td(f"{probs[0][1]}%", style={"padding":"9px 10px","fontSize":"12px","color":color,"fontWeight":"700","fontFamily":"monospace"})
        ], style={"borderBottom":"1px solid #eef2f7"}))

    # Resumen del lote
    resumen_cat = ", ".join(f"{cat} ({n})" for cat, n in conteo_cat.most_common())
    return html.Div(children=[
        html.Div(f"Se clasificaron {len(lineas)} fallas. Distribucion: {resumen_cat}",
                 style={"fontSize":"12.5px","color":"#08374d","fontWeight":"600","backgroundColor":"#e4f7ef",
                        "border":"1px solid #b8e6d3","borderRadius":"8px","padding":"10px 14px","marginBottom":"12px"}),
        html.Table(children=[
            html.Thead(html.Tr(children=[
                html.Th(h, style={"backgroundColor":"#08374d","color":"white","padding":"9px 10px","textAlign":"left","fontSize":"10px","textTransform":"uppercase"})
                for h in ["#","Descripcion","Categoria","Confianza"]])),
            html.Tbody(filas)
        ], style={"width":"100%","borderCollapse":"collapse"})
    ])

# ============================================================
#  CALLBACK: registrar OTM desde el clasificador
# ============================================================
@app.callback(
    Output("otm-resultado-clasif","children"),
    Input("btn-registrar-otm-clasif","n_clicks"),
    [dash.dependencies.State("otm-equipo-clasif","value"),
     dash.dependencies.State("otm-categoria-clasif","data"),
     dash.dependencies.State("otm-descripcion-clasif","data"),
     dash.dependencies.State("sesion","data")],
    prevent_initial_call=True
)
def registrar_otm_clasificador(n, codigo, categoria, descripcion, sesion):
    if not n:
        raise dash.exceptions.PreventUpdate
    # Verificar permisos: solo Supervisor y Tecnico pueden registrar
    rol = "Visualizacion"
    usuario_nombre = "Sistema"
    if sesion and "usuario" in sesion:
        rol = USUARIOS[sesion["usuario"]]["rol"]
        usuario_nombre = USUARIOS[sesion["usuario"]]["nombre"]
    if rol not in ("Supervisor", "Tecnico"):
        return html.Span("No tienes permisos para registrar ordenes de trabajo (requiere rol Supervisor o Tecnico).",
                         style={"color":"#ffd2d2","fontWeight":"600"})
    if not codigo:
        return html.Span("Selecciona un equipo antes de registrar la OTM.", style={"color":"#ffe0b0","fontWeight":"600"})

    # Registrar la OTM con guardado permanente
    try:
        nuevo_id = calculos.agregar_otm(
            codigo=codigo, tipo="Correctivo", categoria=categoria, urgencia="Media",
            descripcion=descripcion if descripcion else "Falla registrada desde el clasificador",
            costo=0, tecnico=usuario_nombre, horas=0, estado_post="Operativo"
        )
        return html.Span(f"✓ OTM registrada correctamente con ID {nuevo_id} para el equipo {codigo}. (Categoria: {categoria})",
                         style={"color":"#c8f7e0","fontWeight":"700"})
    except Exception as e:
        return html.Span(f"Error al registrar la OTM: {str(e)}", style={"color":"#ffd2d2","fontWeight":"600"})

# ============================================================
#  CALLBACK: descargar reporte de automatizacion
# ============================================================
@app.callback(
    Output("descarga-automatizacion","data"),
    [Input("btn-autom-excel","n_clicks"), Input("btn-autom-pdf","n_clicks")],
    prevent_initial_call=True
)
def descargar_automatizacion(clicks_excel, clicks_pdf):
    ctx = dash.callback_context
    if not ctx.triggered or not ctx.triggered[0]["value"]:
        raise dash.exceptions.PreventUpdate
    disparador = ctx.triggered[0]["prop_id"].split(".")[0]
    from datetime import datetime
    fecha = datetime.now().strftime("%Y%m%d")
    stats = automatizacion.estadisticas_globales(historial)
    anomalias = automatizacion.detectar_anomalias(equipos, historial)

    if disparador == "btn-autom-excel":
        df_cat = pd.DataFrame(stats["categorias"])
        df_cat.columns = ["Categoria","Cantidad","Porcentaje","Costo (S/)"]
        df_anom = pd.DataFrame(anomalias) if anomalias else pd.DataFrame([{"info":"Sin anomalias detectadas"}])
        def to_excel(buffer):
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df_cat.to_excel(writer, index=False, sheet_name="Categorias de falla")
                df_anom.to_excel(writer, index=False, sheet_name="Anomalias")
        return dcc.send_bytes(to_excel, f"Automatizacion_BioCare_{fecha}.xlsx")

    if disparador == "btn-autom-pdf":
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        def to_pdf(buffer):
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
            styles = getSampleStyleSheet()
            els = [Paragraph("BioCare Dashboard - Reporte de Automatizacion", styles["Title"])]
            els.append(Paragraph(f"Bioingenieros SAC | INCOR - EsSalud  -  {datetime.now().strftime('%d/%m/%Y')}", styles["Normal"]))
            els.append(Spacer(1, 10))
            els.append(Paragraph(f"Total de fallas correctivas analizadas: {stats['total_fallas']}  |  Costo total: S/ {stats['costo_total']:,.0f}", styles["Normal"]))
            els.append(Spacer(1, 12))
            # Tabla de categorias
            els.append(Paragraph("Distribucion de fallas por categoria", styles["Heading2"]))
            td = [["Categoria","Cantidad","Porcentaje","Costo (S/)"]]
            for c in stats["categorias"]:
                td.append([c["categoria"], str(c["cantidad"]), f"{c['porcentaje']}%", f"{c['costo']:,.0f}"])
            t = Table(td, colWidths=[5*cm,3*cm,3*cm,4*cm])
            t.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#08374d")),
                ("TEXTCOLOR",(0,0),(-1,0),colors.white),
                ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
                ("FONTSIZE",(0,0),(-1,-1),9),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#eef2f7")]),
                ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#cfd9e6")),
                ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ]))
            els.append(t)
            els.append(Spacer(1, 16))
            # Tabla de anomalias
            els.append(Paragraph("Anomalias detectadas (equipos con fallas en aceleracion)", styles["Heading2"]))
            if anomalias:
                ta = [["Codigo","Equipo","Fallas recientes","Ratio"]]
                for a in anomalias:
                    ta.append([a["cod"], a["nombre"][:30], str(a["tasa_reciente"]), f"{a['ratio']}x"])
                t2 = Table(ta, colWidths=[2.5*cm,7*cm,3.5*cm,2.5*cm])
                t2.setStyle(TableStyle([
                    ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#d94862")),
                    ("TEXTCOLOR",(0,0),(-1,0),colors.white),
                    ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
                    ("FONTSIZE",(0,0),(-1,-1),9),
                    ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#fdebef")]),
                    ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#cfd9e6")),
                    ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
                ]))
                els.append(t2)
            else:
                els.append(Paragraph("No se detectaron anomalias en el parque.", styles["Normal"]))
            doc.build(els)
        return dcc.send_bytes(to_pdf, f"Automatizacion_BioCare_{fecha}.pdf")
    raise dash.exceptions.PreventUpdate

# ============================================================
#  CALLBACK: enviar reporte de alertas por correo
# ============================================================
@app.callback(
    Output("estado-correo","children"),
    Input("btn-correo","n_clicks"),
    dash.dependencies.State("correo-destinatario","value"),
    prevent_initial_call=True
)
def enviar_correo_alertas(n, destinatario):
    if not n:
        raise dash.exceptions.PreventUpdate
    # Validar que se ingreso un correo
    if not destinatario or "@" not in destinatario:
        return html.Div("Por favor ingresa un correo destinatario valido.",
                        style={"color":"#d94862","fontWeight":"600"})

    cuerpo = alertas.construir_correo(lista_alertas)
    exito, modo, mensaje = alertas.enviar_reporte_alertas(destinatario, cuerpo)

    if exito and modo == "real":
        color, fondo, borde, icono = "#1f9d6b", "#e4f7ef", "#b8e6d3", "✓"
    elif exito and modo == "demo":
        color, fondo, borde, icono = "#0d5c7d", "#eaf3f7", "#cfe6ec", "✓"
    else:
        color, fondo, borde, icono = "#d94862", "#fdebef", "#f0d0d6", "✗"

    return html.Div(children=[
        html.Span(f"{icono} ", style={"fontWeight":"700"}),
        html.Span(mensaje)
    ], style={"color":color,"backgroundColor":fondo,"border":f"1px solid {borde}",
              "borderRadius":"8px","padding":"10px 14px","fontWeight":"600","lineHeight":"1.5"})

if __name__ == "__main__":
    import os
    # El puerto lo asigna el servicio de hosting (Render) mediante la variable PORT.
    # En local, si no existe, usa el 8050 por defecto.
    puerto = int(os.environ.get("PORT", 8050))
    # El modo debug solo se activa en local (cuando no hay variable PORT del hosting).
    modo_debug = "PORT" not in os.environ
    app.run(host="0.0.0.0", port=puerto, debug=modo_debug)
