# ============================================================
#  BioCare Dashboard - Modulo 5 (PLUS): Automatizacion
#  Reemplaza la busqueda manual del SISMAC con:
#   1. Clasificacion automatica de fallas (machine learning)
#   2. Consulta instantanea del historial de un equipo
#   3. Deteccion de fallas recurrentes
#   4. Resumen automatico por equipo
# ============================================================
import pandas as pd
import numpy as np
import calculos

# ------------------------------------------------------------
#  1. CLASIFICADOR AUTOMATICO DE FALLAS (Machine Learning)
# ------------------------------------------------------------
# Descripciones genericas que un tecnico podria escribir, para
# entrenar el modelo con lenguaje realista (no siempre exacto).
DESCRIPCIONES_GENERICAS = {
 "Electrica":  ["no enciende","se apaga solo","problema de energia","no carga","sin corriente"],
 "Mecanica":   ["hace ruido extrano","no funciona bien","pieza suelta","trabado","vibracion anormal"],
 "Sensores":   ["lectura incorrecta","marca valores raros","no detecta senal","medicion inestable"],
 "Software":   ["se traba la pantalla","error en sistema","no responde","se reinicia solo"],
 "Calibracion":["valores desviados","requiere ajuste","fuera de rango","descalibrado"],
 "Desgaste":   ["equipo muy usado","necesita repuesto","componente gastado","fin de vida util"],
}

def entrenar_clasificador(historial):
    """
    Entrena un modelo TF-IDF + Regresion Logistica que clasifica
    la descripcion de una falla en una de las 6 categorias.
    Devuelve el modelo entrenado y su precision.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import accuracy_score
    from sklearn.pipeline import Pipeline

    corr = historial[historial["tipo_mantenimiento"]=="Correctivo"].copy()
    # Normalizar tildes en las categorias para que coincidan
    corr["cat"] = corr["categoria_falla"].str.replace("é","e").str.replace("á","a").str.replace("í","i").str.replace("ó","o")

    # Construir conjunto de entrenamiento mezclando descripciones reales y genericas
    rng = np.random.default_rng(7)
    descripciones, categorias = [], []
    for _, row in corr.iterrows():
        cat = row["cat"]
        r = rng.random()
        if r < 0.35 and cat in DESCRIPCIONES_GENERICAS:
            # usar descripcion generica (lenguaje de tecnico)
            descripciones.append(str(rng.choice(DESCRIPCIONES_GENERICAS[cat])))
        elif r < 0.43 and cat in DESCRIPCIONES_GENERICAS:
            # ruido: descripcion de otra categoria (error humano real)
            otra = str(rng.choice([k for k in DESCRIPCIONES_GENERICAS if k != cat]))
            descripciones.append(str(rng.choice(DESCRIPCIONES_GENERICAS[otra])))
        else:
            descripciones.append(str(row["descripcion"]))
        categorias.append(cat)

    X = pd.Series(descripciones)
    y = pd.Series(categorias)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    modelo = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1,2), min_df=2)),
        ("clf", LogisticRegression(max_iter=1000, C=5))
    ])
    modelo.fit(Xtr, ytr)
    acc = accuracy_score(yte, modelo.predict(Xte))
    cv = cross_val_score(modelo, X, y, cv=5).mean()
    return modelo, round(acc*100,1), round(cv*100,1)

def clasificar_falla(modelo, texto):
    """Clasifica una descripcion de falla y devuelve categoria + confianza."""
    cat = modelo.predict([texto])[0]
    probs = modelo.predict_proba([texto])[0]
    clases = modelo.classes_
    resultado = sorted(zip(clases, probs), key=lambda x: -x[1])
    return cat, [(c, round(p*100,1)) for c, p in resultado]

# ------------------------------------------------------------
#  2. CONSULTA INSTANTANEA DEL HISTORIAL
# ------------------------------------------------------------
def consultar_historial(historial, codigo):
    """Devuelve todo el historial de un equipo, ordenado por fecha."""
    h = historial[historial["codigo_equipo"]==codigo].sort_values("fecha", ascending=False)
    return h

# ------------------------------------------------------------
#  3. DETECCION DE FALLAS RECURRENTES
# ------------------------------------------------------------
def fallas_recurrentes(historial, codigo):
    """Cuenta las fallas por categoria de un equipo y detecta patrones."""
    corr = historial[(historial["codigo_equipo"]==codigo) &
                     (historial["tipo_mantenimiento"]=="Correctivo")]
    conteo = corr["categoria_falla"].value_counts()
    return conteo

# ------------------------------------------------------------
#  4. RESUMEN AUTOMATICO POR EQUIPO
# ------------------------------------------------------------
def resumen_automatico(equipos, historial, codigo):
    """Genera un resumen en lenguaje natural del estado del equipo."""
    e = equipos[equipos["codigo"]==codigo].iloc[0]
    h = historial[historial["codigo_equipo"]==codigo]
    corr = h[h["tipo_mantenimiento"]=="Correctivo"]
    prev = h[h["tipo_mantenimiento"]=="Preventivo"]
    costo_total = h["costo_soles"].sum()
    antiguedad = 2026 - int(e["anio"])

    recurrentes = corr["categoria_falla"].value_counts()
    if len(recurrentes) > 0:
        max_n = int(recurrentes.iloc[0])
        # Detectar todas las categorias que comparten el valor maximo (empates)
        categorias_top = [cat for cat, n in recurrentes.items() if int(n) == max_n]
    else:
        max_n = 0
        categorias_top = []

    texto = (f"El equipo {e['nombre']} ({codigo}), marca {e['marca']}, opera en "
             f"{e['area']} con {antiguedad} anos de antiguedad. Registra {len(h)} "
             f"intervenciones ({len(prev)} preventivas y {len(corr)} correctivas) "
             f"con un costo acumulado de S/ {costo_total:,.2f}. ")
    if max_n > 0:
        if len(categorias_top) == 1:
            texto += f"Su falla mas recurrente es de tipo {categorias_top[0]}, presentada {max_n} veces."
        elif len(categorias_top) == 2:
            texto += (f"Sus fallas mas recurrentes son de tipo {categorias_top[0]} y {categorias_top[1]}, "
                      f"presentadas {max_n} veces cada una.")
        else:
            lista = ", ".join(categorias_top[:-1]) + f" y {categorias_top[-1]}"
            texto += f"Sus fallas mas recurrentes son de tipo {lista}, presentadas {max_n} veces cada una."
    return texto

def estadisticas_globales(historial):
    """
    Genera estadisticas globales de fallas de todo el parque de equipos:
    distribucion por categoria (cantidad y costo).
    """
    corr = historial[historial["tipo_mantenimiento"]=="Correctivo"]
    total = len(corr)
    conteo = corr["categoria_falla"].value_counts()
    costo = corr.groupby("categoria_falla")["costo_soles"].sum()

    categorias = []
    for cat, n in conteo.items():
        categorias.append({
            "categoria": cat,
            "cantidad": int(n),
            "porcentaje": round(n/total*100, 1) if total > 0 else 0,
            "costo": float(costo.get(cat, 0))
        })
    return {
        "total_fallas": total,
        "categorias": categorias,
        "categoria_top": categorias[0]["categoria"] if categorias else "ninguna",
        "costo_total": float(corr["costo_soles"].sum())
    }

def detectar_anomalias(equipos, historial):
    """
    Detecta equipos con comportamiento atipico: aquellos cuya tasa de fallas
    reciente (ultimos 90 dias) supera significativamente su tasa historica.
    """
    import pandas as pd
    h = historial.copy()
    h["fecha"] = pd.to_datetime(h["fecha"])
    corr = h[h["tipo_mantenimiento"]=="Correctivo"]
    fecha_hoy = pd.Timestamp("2026-05-31")
    anomalias = []
    for cod, g in corr.groupby("codigo_equipo"):
        g = g.sort_values("fecha")
        dias_total = (fecha_hoy - g["fecha"].min()).days
        if dias_total < 180:
            continue
        trimestres = dias_total / 90
        tasa_historica = len(g) / trimestres
        recientes = g[g["fecha"] > fecha_hoy - pd.Timedelta(days=90)]
        tasa_reciente = len(recientes)
        if tasa_historica > 0 and tasa_reciente > tasa_historica * 1.5 and tasa_reciente >= 3:
            nombre = equipos[equipos["codigo"]==cod]["nombre"].values[0]
            ratio = tasa_reciente / tasa_historica
            anomalias.append({
                "cod": cod, "nombre": nombre,
                "tasa_reciente": tasa_reciente,
                "tasa_historica": round(tasa_historica, 1),
                "ratio": round(ratio, 1)
            })
    anomalias.sort(key=lambda x: -x["ratio"])
    return anomalias

def recomendaciones_equipo(equipos, historial, codigo):
    """
    Genera recomendaciones automaticas de mantenimiento en lenguaje natural
    segun el patron de fallas del equipo.
    """
    import pandas as pd
    h = historial.copy()
    h["fecha"] = pd.to_datetime(h["fecha"])
    corr = h[(h["codigo_equipo"]==codigo) & (h["tipo_mantenimiento"]=="Correctivo")]
    recomendaciones = []
    if len(corr) == 0:
        return ["El equipo no registra fallas correctivas. Mantener el plan preventivo actual."]

    recurrentes = corr["categoria_falla"].value_counts()
    cat_top = recurrentes.index[0]
    n_top = int(recurrentes.iloc[0])

    # Recomendacion segun categoria predominante
    mapa_recom = {
        "Calibracion": "Se recomienda revisar el protocolo de calibracion y aumentar su frecuencia (trimestral).",
        "Calibración": "Se recomienda revisar el protocolo de calibracion y aumentar su frecuencia (trimestral).",
        "Sensores": "Se recomienda inspeccionar y considerar el reemplazo preventivo de los sensores criticos.",
        "Electrica": "Se recomienda una revision del sistema electrico y de las conexiones de alimentacion.",
        "Eléctrica": "Se recomienda una revision del sistema electrico y de las conexiones de alimentacion.",
        "Mecanica": "Se recomienda revisar las partes mecanicas moviles y la lubricacion de componentes.",
        "Mecánica": "Se recomienda revisar las partes mecanicas moviles y la lubricacion de componentes.",
        "Software": "Se recomienda actualizar el firmware y verificar la configuracion del software.",
        "Desgaste": "Se recomienda programar el reemplazo de piezas de desgaste segun la vida util del fabricante.",
    }
    recomendaciones.append(mapa_recom.get(cat_top, "Se recomienda una revision tecnica general del equipo."))

    # Recomendacion segun frecuencia de fallas
    fecha_hoy = pd.Timestamp("2026-05-31")
    recientes = corr[corr["fecha"] > fecha_hoy - pd.Timedelta(days=90)]
    if len(recientes) >= 3:
        recomendaciones.append(f"Atencion: {len(recientes)} fallas en los ultimos 90 dias. Evaluar una intervencion mayor o el reemplazo del equipo.")

    # Recomendacion segun costo
    costo_corr = corr["costo_soles"].sum()
    if costo_corr > 30000:
        recomendaciones.append(f"El costo correctivo acumulado (S/ {costo_corr:,.0f}) es elevado. Analizar la relacion costo-beneficio frente a un equipo nuevo.")

    return recomendaciones

def tendencia_temporal_fallas(historial):
    """Devuelve la evolucion de las categorias de falla por anio."""
    import pandas as pd
    h = historial.copy()
    h["fecha"] = pd.to_datetime(h["fecha"])
    corr = h[h["tipo_mantenimiento"]=="Correctivo"]
    tabla = corr.groupby([corr["fecha"].dt.year, "categoria_falla"]).size().unstack(fill_value=0)
    return tabla

def fallas_por_area(equipos, historial):
    """Devuelve la distribucion de categorias de falla por area clinica."""
    import pandas as pd
    h = historial.copy()
    corr = h[h["tipo_mantenimiento"]=="Correctivo"].merge(equipos[["codigo","area"]], left_on="codigo_equipo", right_on="codigo")
    tabla = corr.groupby(["area","categoria_falla"]).size().unstack(fill_value=0)
    return tabla

# Prueba
if __name__ == "__main__":
    equipos, historial = calculos.cargar_datos()
    print("Entrenando clasificador de fallas...")
    modelo, acc, cv = entrenar_clasificador(historial)
    print(f"  Precision (test): {acc}%")
    print(f"  Precision (validacion cruzada): {cv}%")
    print("\nPrueba de clasificacion:")
    for txt in ["no enciende ni con el cargador","la pantalla se queda congelada","marca valores de presion raros"]:
        cat, probs = clasificar_falla(modelo, txt)
        print(f"  '{txt}' -> {cat} ({probs[0][1]}%)")
    print("\nResumen automatico EQ-001:")
    print(" ", resumen_automatico(equipos, historial, "EQ-001"))
    print("\nFallas recurrentes EQ-001:")
    print(fallas_recurrentes(historial, "EQ-001").to_string())
