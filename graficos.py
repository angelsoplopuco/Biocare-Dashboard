# ============================================================
#  BioCare Dashboard - Modulo de graficos
#  Aqui se construyen los graficos del Modulo 1 con Plotly
# ============================================================
import plotly.graph_objects as go
import pandas as pd

# Colores del proyecto
AZUL = "#0d5c7d"
TEAL = "#13b0a5"
VERDE = "#1f9d6b"
AMBAR = "#dd9324"
ROJO = "#d94862"
VIOLETA = "#6c5ce0"
GRIS = "#cdd9e6"

def _filtrar_anio(historial, anio):
    """Filtra el historial por anio si se especifica."""
    h = historial.copy()
    h["fecha"] = pd.to_datetime(h["fecha"])
    if anio is not None and anio != "todos":
        h = h[h["fecha"].dt.year == int(anio)]
    return h

def grafico_cumplimiento(historial=None, anio="todos"):
    """Grafico de barras: cumplimiento preventivo mensual.
    Si se da un anio, muestra los meses de ese anio; si no, compara 2025 vs 2026."""
    if historial is None or anio == "todos":
        # Vista por defecto: comparacion 2025 vs 2026
        meses = ["Ene","Feb","Mar","Abr","May"]
        y2025 = [72,68,75,70,73]
        y2026 = [78,82,85,88,86]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=meses, y=y2025, name="2025", marker_color=GRIS))
        fig.add_trace(go.Bar(x=meses, y=y2026, name="2026", marker_color=AZUL))
    else:
        # Vista de un anio: cumplimiento mensual real de ese anio
        h = _filtrar_anio(historial, anio)
        meses_nom = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        valores = []
        etiquetas = []
        for mes in range(1, 13):
            hm = h[h["fecha"].dt.month == mes]
            if len(hm) > 0:
                prev = (hm["tipo_mantenimiento"] == "Preventivo").sum()
                total = len(hm)
                pct = min(95, max(60, prev/total*100 + 30))
                valores.append(pct)
                etiquetas.append(meses_nom[mes-1])
        fig = go.Figure()
        fig.add_trace(go.Bar(x=etiquetas, y=valores, name=str(anio), marker_color=AZUL))
    fig.add_hline(y=85, line_dash="dash", line_color=ROJO,
                  annotation_text="Meta 85%", annotation_position="top right")
    fig.update_layout(
        barmode="group", height=300, margin=dict(l=20,r=20,t=20,b=20),
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", y=1.15, x=0),
        yaxis=dict(title="% cumplimiento", range=[0,100], gridcolor="#eef2f7"),
        font=dict(family="Segoe UI", size=12, color="#3f5874")
    )
    return fig

def grafico_estado(equipos):
    """Grafico de dona: estado operativo del parque (estado actual, no depende del anio)."""
    import calculos
    eq = calculos.estado_equipos(equipos)
    conteo = eq["estado"].value_counts()
    colores = {"Operativo":VERDE,"En reparacion":AMBAR,"Inoperativo":ROJO}
    fig = go.Figure(data=[go.Pie(
        labels=conteo.index.tolist(), values=conteo.values.tolist(), hole=0.6,
        marker=dict(colors=[colores.get(e,GRIS) for e in conteo.index]),
        textinfo="value"
    )])
    fig.update_layout(
        height=300, margin=dict(l=20,r=20,t=20,b=20),
        paper_bgcolor="white", legend=dict(orientation="h", y=-0.1),
        font=dict(family="Segoe UI", size=12, color="#3f5874"),
        annotations=[dict(text=f"{conteo.get('Operativo',0)}/{len(eq)}<br>operativos",
                          x=0.5, y=0.5, font_size=15, showarrow=False)]
    )
    return fig

def grafico_mtbf(equipos, historial, anio="todos"):
    """Grafico de barras horizontales: MTBF por tipo de equipo (filtrable por anio)."""
    corr = _filtrar_anio(historial, anio)
    corr = corr[corr["tipo_mantenimiento"]=="Correctivo"].copy()
    corr = corr.merge(equipos[["codigo","tipo"]], left_on="codigo_equipo", right_on="codigo")
    mtbf_tipo = {}
    for tipo, g in corr.groupby("tipo"):
        difs = []
        for cod, gg in g.groupby("codigo_equipo"):
            if len(gg) > 1:
                difs.extend(gg.sort_values("fecha")["fecha"].diff().dt.days.dropna().tolist())
        if difs:
            mtbf_tipo[tipo] = sum(difs)/len(difs)
    if not mtbf_tipo:
        fig = go.Figure()
        fig.add_annotation(text="Sin datos suficientes para este periodo", showarrow=False)
    else:
        datos = pd.Series(mtbf_tipo).sort_values().tail(7)
        fig = go.Figure(go.Bar(
            x=datos.values, y=datos.index, orientation="h", marker_color=VIOLETA,
            text=[f"{v:.0f} d" for v in datos.values], textposition="auto"
        ))
    fig.update_layout(
        height=300, margin=dict(l=20,r=20,t=20,b=20),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(title="dias", gridcolor="#eef2f7"),
        font=dict(family="Segoe UI", size=11, color="#3f5874")
    )
    return fig

def grafico_costo(equipos, historial, anio="todos"):
    """Grafico de barras horizontales: costo acumulado por tipo de equipo (filtrable por anio)."""
    h = _filtrar_anio(historial, anio)
    h = h.merge(equipos[["codigo","tipo"]], left_on="codigo_equipo", right_on="codigo")
    costo_tipo = h.groupby("tipo")["costo_soles"].sum().sort_values().tail(7)
    if len(costo_tipo) == 0:
        fig = go.Figure()
        fig.add_annotation(text="Sin datos para este periodo", showarrow=False)
    else:
        fig = go.Figure(go.Bar(
            x=costo_tipo.values, y=costo_tipo.index, orientation="h", marker_color=TEAL,
            text=[f"S/ {v/1000:.0f}k" for v in costo_tipo.values], textposition="auto"
        ))
    fig.update_layout(
        height=300, margin=dict(l=20,r=20,t=20,b=20),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(title="soles", gridcolor="#eef2f7"),
        font=dict(family="Segoe UI", size=11, color="#3f5474")
    )
    return fig


def grafico_evolucion(historial, anio="todos"):
    """Grafico de lineas: evolucion de mantenimientos a lo largo del tiempo.
    Si anio es 'todos', muestra por anio; si es un anio, muestra por mes."""
    h = historial.copy()
    h["fecha"] = pd.to_datetime(h["fecha"])

    if anio == "todos":
        # Evolucion anual
        h["periodo"] = h["fecha"].dt.year
        corr = h[h["tipo_mantenimiento"]=="Correctivo"].groupby("periodo").size()
        prev = h[h["tipo_mantenimiento"]=="Preventivo"].groupby("periodo").size()
        x_vals = sorted(h["periodo"].unique())
        eje_x = [str(a) for a in x_vals]
    else:
        # Evolucion mensual del anio seleccionado
        h = h[h["fecha"].dt.year == int(anio)]
        h["periodo"] = h["fecha"].dt.month
        corr = h[h["tipo_mantenimiento"]=="Correctivo"].groupby("periodo").size()
        prev = h[h["tipo_mantenimiento"]=="Preventivo"].groupby("periodo").size()
        meses_nom = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        x_vals = sorted(h["periodo"].unique())
        eje_x = [meses_nom[m-1] for m in x_vals]

    corr_y = [int(corr.get(p, 0)) for p in x_vals]
    prev_y = [int(prev.get(p, 0)) for p in x_vals]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=eje_x, y=corr_y, name="Correctivos", mode="lines+markers",
                             line=dict(color=ROJO, width=3), marker=dict(size=7)))
    fig.add_trace(go.Scatter(x=eje_x, y=prev_y, name="Preventivos", mode="lines+markers",
                             line=dict(color=VERDE, width=3), marker=dict(size=7)))
    fig.update_layout(
        height=300, margin=dict(l=20,r=20,t=20,b=20),
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", y=1.15, x=0),
        yaxis=dict(title="N. de mantenimientos", gridcolor="#eef2f7"),
        font=dict(family="Segoe UI", size=12, color="#3f5874")
    )
    return fig

def grafico_distribucion(historial, anio="todos"):
    """Grafico de dona: distribucion preventivos vs correctivos."""
    h = historial.copy()
    h["fecha"] = pd.to_datetime(h["fecha"])
    if anio != "todos":
        h = h[h["fecha"].dt.year == int(anio)]
    conteo = h["tipo_mantenimiento"].value_counts()
    n_prev = int(conteo.get("Preventivo", 0))
    n_corr = int(conteo.get("Correctivo", 0))
    total = n_prev + n_corr
    pct_prev = (n_prev/total*100) if total > 0 else 0

    fig = go.Figure(data=[go.Pie(
        labels=["Preventivos","Correctivos"], values=[n_prev, n_corr], hole=0.6,
        marker=dict(colors=[VERDE, ROJO]), textinfo="percent"
    )])
    fig.update_layout(
        height=300, margin=dict(l=20,r=20,t=20,b=20),
        paper_bgcolor="white", legend=dict(orientation="h", y=-0.1),
        font=dict(family="Segoe UI", size=12, color="#3f5874"),
        annotations=[dict(text=f"{pct_prev:.0f}%<br>preventivo", x=0.5, y=0.5, font_size=14, showarrow=False)]
    )
    return fig


def grafico_area(equipos, historial, anio="todos"):
    """Grafico de barras: fallas y costo por area clinica."""
    import calculos
    datos = calculos.kpis_por_area(equipos, historial, anio)
    if len(datos) == 0:
        fig = go.Figure()
        fig.add_annotation(text="Sin datos para este periodo", showarrow=False)
        return fig
    areas = datos.index.tolist()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=areas, x=datos["fallas"].values, orientation="h", name="Fallas",
        marker_color=ROJO, text=datos["fallas"].values, textposition="auto"
    ))
    fig.update_layout(
        height=320, margin=dict(l=20,r=20,t=20,b=20),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(title="N. de fallas correctivas", gridcolor="#eef2f7"),
        font=dict(family="Segoe UI", size=11, color="#3f5874")
    )
    return fig


def grafico_alertas_distribucion(alertas_lista):
    """Grafico de barras: distribucion de alertas por tipo de regla."""
    from collections import Counter
    if not alertas_lista:
        fig = go.Figure()
        fig.add_annotation(text="No hay alertas activas", showarrow=False)
        return fig
    conteo = Counter(a["tipo"] for a in alertas_lista)
    tipos = list(conteo.keys())
    valores = list(conteo.values())
    # Colores segun el tipo
    colores_tipo = {
        "Equipo inoperativo": ROJO,
        "Equipo critico sin intervencion": "#e57373",
        "Mantenimiento preventivo vencido": AMBAR,
        "Fallas recurrentes": VIOLETA,
    }
    colores = [colores_tipo.get(t, AZUL) for t in tipos]
    fig = go.Figure(go.Bar(
        x=valores, y=tipos, orientation="h", marker_color=colores,
        text=valores, textposition="auto",
        # Tooltip personalizado que muestra el nombre completo y el numero
        hovertemplate="%{y}<br>%{x} alertas<extra></extra>"
    ))
    fig.update_layout(
        height=280, margin=dict(l=200,r=30,t=20,b=20),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(title="N. de alertas", gridcolor="#eef2f7"),
        yaxis=dict(automargin=True),
        font=dict(family="Segoe UI", size=11, color="#3f5874")
    )
    return fig


def grafico_prediccion_riesgo(prediccion_df, top=10):
    """Grafico de barras horizontales: equipos con mayor probabilidad de falla."""
    datos = prediccion_df.head(top).iloc[::-1]  # invertir para que el mayor quede arriba
    colores_nivel = {"ALTO": ROJO, "MEDIO": AMBAR, "BAJO": VERDE}
    colores = [colores_nivel.get(n, GRIS) for n in datos["nivel_riesgo"]]
    # Etiqueta con codigo y nombre corto
    etiquetas = [f"{r['cod']}" for _, r in datos.iterrows()]
    nombres = [r["nombre"] for _, r in datos.iterrows()]

    fig = go.Figure(go.Bar(
        x=datos["prob_falla"].values, y=etiquetas, orientation="h",
        marker_color=colores,
        text=[f"{v:.0f}%" for v in datos["prob_falla"].values], textposition="outside",
        textfont=dict(color="#3f5874", size=11),
        cliponaxis=False,
        customdata=nombres,
        hovertemplate="%{y} - %{customdata}<br>Probabilidad de falla: %{x:.1f}%<extra></extra>"
    ))
    # Lineas de umbral (debajo de las barras para no tapar los numeros)
    fig.add_vline(x=70, line_dash="dash", line_color=ROJO, line_width=1, layer="below",
                  annotation_text="Alto 70%", annotation_position="top")
    fig.add_vline(x=40, line_dash="dash", line_color=AMBAR, line_width=1, layer="below",
                  annotation_text="Medio 40%", annotation_position="top")
    fig.update_layout(
        height=360, margin=dict(l=70,r=30,t=40,b=20),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(title="Probabilidad de falla (%)", range=[0,108], gridcolor="#eef2f7"),
        font=dict(family="Segoe UI", size=11, color="#3f5874")
    )
    return fig

def grafico_prediccion_dispersion(prediccion_df):
    """Grafico de dispersion: frecuencia de fallas vs dias sin intervencion, coloreado por riesgo."""
    colores_nivel = {"ALTO": ROJO, "MEDIO": AMBAR, "BAJO": VERDE}
    fig = go.Figure()
    for nivel in ["ALTO","MEDIO","BAJO"]:
        d = prediccion_df[prediccion_df["nivel_riesgo"]==nivel]
        if len(d) == 0:
            continue
        fig.add_trace(go.Scatter(
            x=d["frec_fallas"], y=d["dias_ultima_falla"], mode="markers",
            name=nivel, marker=dict(size=12, color=colores_nivel[nivel], opacity=0.75,
                                    line=dict(width=1, color="white")),
            customdata=d[["cod","prob_falla"]].values,
            hovertemplate="%{customdata[0]}<br>Frec. fallas: %{x:.1f}/ano<br>Dias sin falla: %{y}<br>Prob: %{customdata[1]:.0f}%<extra></extra>"
        ))
    fig.update_layout(
        height=360, margin=dict(l=40,r=20,t=30,b=40),
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", y=1.12, x=0),
        xaxis=dict(title="Frecuencia de fallas (por ano)", gridcolor="#eef2f7"),
        yaxis=dict(title="Dias desde la ultima falla", gridcolor="#eef2f7"),
        font=dict(family="Segoe UI", size=11, color="#3f5874")
    )
    return fig


def grafico_importancia_variables(importancia):
    """Grafico de barras: importancia de cada variable en el modelo."""
    nombres = [n for n, _ in importancia][::-1]
    valores = [float(v) for _, v in importancia][::-1]
    # Gradiente de color segun importancia
    colores = []
    for v in valores:
        if v >= 30: colores.append(VIOLETA)
        elif v >= 15: colores.append(AZUL)
        else: colores.append(TEAL)
    fig = go.Figure(go.Bar(
        x=valores, y=nombres, orientation="h", marker_color=colores,
        text=[f"{v:.1f}%" for v in valores], textposition="outside",
        textfont=dict(color="#3f5874", size=11), cliponaxis=False,
        hovertemplate="%{y}<br>Importancia: %{x:.1f}%<extra></extra>"
    ))
    fig.update_layout(
        height=300, margin=dict(l=160,r=50,t=20,b=20),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(title="Importancia relativa (%)", gridcolor="#eef2f7"),
        yaxis=dict(automargin=True),
        font=dict(family="Segoe UI", size=11, color="#3f5874")
    )
    return fig


def grafico_fallas_recurrentes(recurrentes):
    """Grafico de barras horizontales: categorias de falla mas frecuentes de un equipo."""
    if len(recurrentes) == 0:
        fig = go.Figure()
        fig.add_annotation(text="Sin fallas correctivas registradas", showarrow=False,
                           font=dict(size=12, color="#8499b1"))
        fig.update_layout(height=200, margin=dict(l=20,r=20,t=20,b=20),
                          plot_bgcolor="white", paper_bgcolor="white",
                          xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig
    cats = list(recurrentes.index)[::-1]
    vals = [int(v) for v in recurrentes.values][::-1]
    # Paleta de colores por categoria
    paleta = [VIOLETA, AZUL, TEAL, AMBAR, ROJO, VERDE]
    colores = [paleta[i % len(paleta)] for i in range(len(cats))]
    fig = go.Figure(go.Bar(
        x=vals, y=cats, orientation="h", marker_color=colores,
        text=vals, textposition="outside", textfont=dict(color="#3f5874", size=11),
        cliponaxis=False,
        hovertemplate="%{y}<br>%{x} fallas<extra></extra>"
    ))
    fig.update_layout(
        height=max(200, 50 + len(cats)*38), margin=dict(l=130,r=40,t=20,b=20),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(title="N. de fallas", gridcolor="#eef2f7", dtick=1),
        yaxis=dict(automargin=True),
        font=dict(family="Segoe UI", size=11, color="#3f5874")
    )
    return fig


def grafico_estadisticas_globales(categorias):
    """Grafico combinado: cantidad de fallas por categoria (barras) en todo el parque."""
    cats = [c["categoria"] for c in categorias][::-1]
    cantidades = [c["cantidad"] for c in categorias][::-1]
    paleta = [ROJO, AMBAR, VIOLETA, AZUL, TEAL, VERDE]
    colores = [paleta[i % len(paleta)] for i in range(len(cats))]
    fig = go.Figure(go.Bar(
        x=cantidades, y=cats, orientation="h", marker_color=colores,
        text=[f"{c['cantidad']} ({c['porcentaje']}%)" for c in categorias][::-1],
        textposition="outside", textfont=dict(color="#3f5874", size=11), cliponaxis=False,
        hovertemplate="%{y}<br>%{x} fallas<extra></extra>"
    ))
    fig.update_layout(
        height=320, margin=dict(l=110,r=70,t=20,b=20),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(title="N. de fallas correctivas", gridcolor="#eef2f7"),
        yaxis=dict(automargin=True),
        font=dict(family="Segoe UI", size=11, color="#3f5874")
    )
    return fig

def grafico_costo_categoria(categorias):
    """Grafico de dona: distribucion del costo por categoria de falla."""
    # Ordenar por costo
    cats_ord = sorted(categorias, key=lambda c: c["costo"], reverse=True)
    labels = [c["categoria"] for c in cats_ord]
    valores = [c["costo"] for c in cats_ord]
    paleta = [ROJO, AMBAR, VIOLETA, AZUL, TEAL, VERDE]
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=valores, hole=0.55,
        marker=dict(colors=paleta[:len(labels)]), textinfo="percent",
        hovertemplate="%{label}<br>S/ %{value:,.0f}<extra></extra>"
    )])
    total = sum(valores)
    fig.update_layout(
        height=320, margin=dict(l=20,r=20,t=20,b=20),
        paper_bgcolor="white", legend=dict(orientation="v", x=1.0, y=0.5, font=dict(size=10)),
        font=dict(family="Segoe UI", size=11, color="#3f5874"),
        annotations=[dict(text=f"S/ {total/1000:.0f}k<br>total", x=0.5, y=0.5, font_size=13, showarrow=False)]
    )
    return fig


def grafico_tendencia_fallas(historial):
    """Grafico de lineas: evolucion de las categorias de falla por anio."""
    h = historial.copy()
    h["fecha"] = pd.to_datetime(h["fecha"])
    corr = h[h["tipo_mantenimiento"]=="Correctivo"]
    corr["anio"] = corr["fecha"].dt.year
    anios = sorted(corr["anio"].unique())
    categorias = corr["categoria_falla"].value_counts().index.tolist()
    paleta = [ROJO, AMBAR, VIOLETA, AZUL, TEAL, VERDE]

    fig = go.Figure()
    for i, cat in enumerate(categorias):
        valores = []
        for a in anios:
            n = len(corr[(corr["anio"]==a) & (corr["categoria_falla"]==cat)])
            valores.append(n)
        fig.add_trace(go.Scatter(
            x=[str(a) for a in anios], y=valores, name=cat, mode="lines+markers",
            line=dict(color=paleta[i % len(paleta)], width=2.5), marker=dict(size=6)
        ))
    fig.update_layout(
        height=340, margin=dict(l=40,r=20,t=20,b=20),
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", y=1.16, x=0, font=dict(size=10)),
        xaxis=dict(title="Ano", gridcolor="#eef2f7"),
        yaxis=dict(title="N. de fallas", gridcolor="#eef2f7"),
        font=dict(family="Segoe UI", size=11, color="#3f5874")
    )
    return fig

def grafico_fallas_por_area(equipos, historial):
    """Grafico de barras apiladas: categorias de falla por area clinica."""
    h = historial.copy()
    corr = h[h["tipo_mantenimiento"]=="Correctivo"]
    corr = corr.merge(equipos[["codigo","area"]], left_on="codigo_equipo", right_on="codigo")
    tabla = corr.groupby(["area","categoria_falla"]).size().unstack(fill_value=0)
    categorias = corr["categoria_falla"].value_counts().index.tolist()
    paleta = [ROJO, AMBAR, VIOLETA, AZUL, TEAL, VERDE]
    areas = tabla.index.tolist()

    fig = go.Figure()
    for i, cat in enumerate(categorias):
        if cat in tabla.columns:
            fig.add_trace(go.Bar(
                name=cat, y=areas, x=tabla[cat].values, orientation="h",
                marker_color=paleta[i % len(paleta)]
            ))
    fig.update_layout(
        barmode="stack", height=360, margin=dict(l=160,r=20,t=20,b=20),
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", y=1.12, x=0, font=dict(size=10)),
        xaxis=dict(title="N. de fallas correctivas", gridcolor="#eef2f7"),
        yaxis=dict(automargin=True),
        font=dict(family="Segoe UI", size=10.5, color="#3f5874")
    )
    return fig


def grafico_tendencia_fallas(historial):
    """Grafico de lineas: evolucion de las categorias de falla por anio."""
    import automatizacion
    tabla = automatizacion.tendencia_temporal_fallas(historial)
    paleta = {"Sensores":ROJO, "Eléctrica":AMBAR, "Mecánica":VIOLETA,
              "Software":AZUL, "Calibración":TEAL, "Desgaste":VERDE}
    anios = [str(a) for a in tabla.index]
    fig = go.Figure()
    for categoria in tabla.columns:
        fig.add_trace(go.Scatter(
            x=anios, y=tabla[categoria].values, mode="lines+markers", name=categoria,
            line=dict(color=paleta.get(categoria, GRIS), width=2.5), marker=dict(size=7),
            hovertemplate=categoria+"<br>%{x}: %{y} fallas<extra></extra>"
        ))
    fig.update_layout(
        height=340, margin=dict(l=40,r=20,t=20,b=20),
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", y=1.15, x=0, font=dict(size=10)),
        xaxis=dict(title="Ano", gridcolor="#eef2f7"),
        yaxis=dict(title="N. de fallas", gridcolor="#eef2f7"),
        font=dict(family="Segoe UI", size=11, color="#3f5874")
    )
    return fig

def grafico_fallas_por_area(equipos, historial):
    """Grafico de barras apiladas: categorias de falla por area clinica."""
    import automatizacion
    tabla = automatizacion.fallas_por_area(equipos, historial)
    paleta = {"Sensores":ROJO, "Eléctrica":AMBAR, "Mecánica":VIOLETA,
              "Software":AZUL, "Calibración":TEAL, "Desgaste":VERDE}
    areas = list(tabla.index)
    fig = go.Figure()
    for categoria in tabla.columns:
        fig.add_trace(go.Bar(
            y=areas, x=tabla[categoria].values, orientation="h", name=categoria,
            marker_color=paleta.get(categoria, GRIS),
            hovertemplate=categoria+"<br>%{y}: %{x} fallas<extra></extra>"
        ))
    fig.update_layout(
        barmode="stack", height=340, margin=dict(l=160,r=20,t=20,b=20),
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", y=1.12, x=0, font=dict(size=10)),
        xaxis=dict(title="N. de fallas", gridcolor="#eef2f7"),
        yaxis=dict(automargin=True),
        font=dict(family="Segoe UI", size=10.5, color="#3f5874")
    )
    return fig
