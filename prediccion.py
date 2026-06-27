# ============================================================
#  BioCare Dashboard - Modulo 4: Modelo Predictivo
#  Estima la probabilidad de que cada equipo falle en los
#  proximos 30-60 dias usando regresion logistica.
# ============================================================
import pandas as pd
import numpy as np
import calculos

FECHA_HOY = pd.Timestamp("2026-05-31")

def construir_caracteristicas(equipos, historial):
    """
    Para cada equipo calcula variables (caracteristicas) que ayudan
    a predecir una falla proxima:
    - frecuencia historica de fallas
    - dias desde la ultima falla
    - antiguedad del equipo
    - indice de criticidad
    - costo promedio de reparacion
    """
    criticidad = calculos.calcular_criticidad(equipos, historial)
    idx_por_eq = dict(zip(criticidad["cod"], criticidad["indice"]))
    corr = historial[historial["tipo_mantenimiento"]=="Correctivo"]
    anios = (historial["fecha"].max() - historial["fecha"].min()).days / 365

    filas = []
    for _, e in equipos.iterrows():
        cod = e["codigo"]
        g = corr[corr["codigo_equipo"]==cod].sort_values("fecha")
        n_fallas = len(g)
        frec = n_fallas / anios
        if len(g) > 0:
            dias_ultima = (FECHA_HOY - g["fecha"].max()).days
            costo_prom = g["costo_soles"].mean()
        else:
            dias_ultima = 999
            costo_prom = 0
        antiguedad = 2026 - int(e["anio"])
        idx = idx_por_eq.get(cod, 0)
        filas.append({
            "cod": cod, "nombre": e["nombre"],
            "frec_fallas": round(frec,2), "dias_ultima_falla": dias_ultima,
            "antiguedad": antiguedad, "indice_crit": idx,
            "costo_prom": round(float(costo_prom),2)
        })
    return pd.DataFrame(filas)

def entrenar_y_predecir(equipos, historial):
    """
    Entrena un modelo de regresion logistica y devuelve la
    probabilidad de falla proxima para cada equipo.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    df = construir_caracteristicas(equipos, historial)

    # Variable objetivo (simulada con criterio realista):
    # un equipo se considera "en riesgo" si tiene alta frecuencia de fallas
    # Y hace tiempo que no se interviene. Esto crea el patron a aprender.
    df["riesgo"] = (
        (df["frec_fallas"] > df["frec_fallas"].median()) &
        (df["dias_ultima_falla"] > 25)
    ).astype(int)

    X = df[["frec_fallas","dias_ultima_falla","antiguedad","indice_crit","costo_prom"]].values
    y = df["riesgo"].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    modelo = LogisticRegression(max_iter=1000)
    modelo.fit(X_scaled, y)

    # Probabilidad de falla proxima (clase 1)
    df["prob_falla"] = (modelo.predict_proba(X_scaled)[:,1] * 100).round(1)

    # Horizonte estimado: a mayor probabilidad, menor cantidad de dias
    df["horizonte_dias"] = df["prob_falla"].apply(
        lambda p: 30 if p >= 70 else (45 if p >= 40 else 60)
    )

    # Nivel de riesgo segun probabilidad
    def nivel(p):
        if p >= 70: return "ALTO"
        if p >= 40: return "MEDIO"
        return "BAJO"
    df["nivel_riesgo"] = df["prob_falla"].apply(nivel)

    return df.sort_values("prob_falla", ascending=False)

# Prueba
if __name__ == "__main__":
    equipos, historial = calculos.cargar_datos()
    pred = entrenar_y_predecir(equipos, historial)
    print("Prediccion de falla proxima (top 8):")
    print(f"{'Equipo':<8}{'Nombre':<28}{'Prob.':>7}{'Horiz.':>8}{'Riesgo':>8}")
    for _, r in pred.head(8).iterrows():
        print(f"{r['cod']:<8}{r['nombre'][:26]:<28}{r['prob_falla']:>6.1f}%{r['horizonte_dias']:>6}d{r['nivel_riesgo']:>9}")
    print(f"\nEquipos en riesgo ALTO: {(pred['nivel_riesgo']=='ALTO').sum()}")
    print(f"Equipos en riesgo MEDIO: {(pred['nivel_riesgo']=='MEDIO').sum()}")
    print(f"Equipos en riesgo BAJO: {(pred['nivel_riesgo']=='BAJO').sum()}")


def factores_prediccion(prediccion_df, codigo):
    """
    Interpreta los factores que influyen en la prediccion de un equipo.
    Devuelve una lista de factores con su valor, nivel de impacto y explicacion.
    """
    fila = prediccion_df[prediccion_df["cod"]==codigo]
    if len(fila) == 0:
        return None
    r = fila.iloc[0]

    # Calcular percentiles para contextualizar cada factor
    def nivel_impacto(valor, serie, mayor_es_peor=True):
        pct = (serie < valor).mean() * 100
        if not mayor_es_peor:
            pct = 100 - pct
        if pct >= 66:
            return "ALTO", "#d94862"
        elif pct >= 33:
            return "MEDIO", "#dd9324"
        else:
            return "BAJO", "#1f9d6b"

    factores = []
    # Frecuencia de fallas
    imp, col = nivel_impacto(r["frec_fallas"], prediccion_df["frec_fallas"], True)
    factores.append({
        "nombre": "Frecuencia de fallas",
        "valor": f"{r['frec_fallas']:.1f} fallas/ano",
        "impacto": imp, "color": col,
        "explicacion": "Cuantas veces falla el equipo al ano. Mas fallas indican mayor probabilidad de falla futura."
    })
    # Dias desde la ultima falla
    imp, col = nivel_impacto(r["dias_ultima_falla"], prediccion_df["dias_ultima_falla"], True)
    factores.append({
        "nombre": "Dias desde la ultima falla",
        "valor": f"{int(r['dias_ultima_falla'])} dias",
        "impacto": imp, "color": col,
        "explicacion": "Tiempo sin intervencion. Mucho tiempo sin revision aumenta el riesgo acumulado."
    })
    # Antiguedad
    imp, col = nivel_impacto(r["antiguedad"], prediccion_df["antiguedad"], True)
    factores.append({
        "nombre": "Antiguedad del equipo",
        "valor": f"{int(r['antiguedad'])} anos",
        "impacto": imp, "color": col,
        "explicacion": "Anos de uso. Los equipos mas antiguos tienen mayor desgaste y riesgo."
    })
    # Indice de criticidad
    imp, col = nivel_impacto(r["indice_crit"], prediccion_df["indice_crit"], True)
    factores.append({
        "nombre": "Indice de criticidad",
        "valor": f"{int(r['indice_crit'])}/100",
        "impacto": imp, "color": col,
        "explicacion": "Importancia clinica del equipo. Equipos criticos se priorizan en el analisis."
    })
    # Costo promedio
    imp, col = nivel_impacto(r["costo_prom"], prediccion_df["costo_prom"], True)
    factores.append({
        "nombre": "Costo promedio de reparacion",
        "valor": f"S/ {r['costo_prom']:.0f}",
        "impacto": imp, "color": col,
        "explicacion": "Costo tipico de cada reparacion. Refleja la complejidad del mantenimiento."
    })
    return r, factores


def evaluar_modelo(equipos, historial):
    """
    Entrena el modelo y devuelve sus metricas de rendimiento y la
    importancia de las variables. Para mostrar la calidad del modelo.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score
    from sklearn.metrics import confusion_matrix, accuracy_score
    import numpy as np

    df = construir_caracteristicas(equipos, historial)
    df["riesgo"] = ((df["frec_fallas"] > df["frec_fallas"].median()) & (df["dias_ultima_falla"] > 25)).astype(int)

    X = df[["frec_fallas","dias_ultima_falla","antiguedad","indice_crit","costo_prom"]].values
    y = df["riesgo"].values
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    modelo = LogisticRegression(max_iter=1000)
    modelo.fit(Xs, y)
    pred = modelo.predict(Xs)

    acc = round(accuracy_score(y, pred) * 100, 1)
    cv = round(cross_val_score(modelo, Xs, y, cv=5).mean() * 100, 1)
    cm = confusion_matrix(y, pred)

    # Importancia de variables (basada en los coeficientes)
    nombres = ["Frecuencia de fallas","Dias sin intervencion","Antiguedad","Indice de criticidad","Costo promedio"]
    importancias = np.abs(modelo.coef_[0])
    importancias_norm = (importancias / importancias.sum() * 100).round(1)
    importancia = sorted(zip(nombres, importancias_norm), key=lambda x: -x[1])

    return {
        "accuracy": acc,
        "cv": cv,
        "matriz": cm.tolist(),
        "importancia": importancia,
        "n_riesgo": int(y.sum()),
        "n_total": len(y)
    }


def cronograma_mantenimiento(prediccion_df, top=10):
    """
    Genera un cronograma de mantenimiento sugerido, priorizando equipos
    por nivel de riesgo y horizonte de falla. Calcula una fecha sugerida.
    """
    from datetime import timedelta
    # Ordenar por probabilidad de falla (mayor primero)
    df = prediccion_df.sort_values("prob_falla", ascending=False).head(top)
    cronograma = []
    fecha_base = FECHA_HOY
    for i, (_, r) in enumerate(df.iterrows()):
        # La fecha sugerida depende del horizonte: a mayor riesgo, antes
        if r["nivel_riesgo"] == "ALTO":
            dias_para_atender = 7 + i * 2
        elif r["nivel_riesgo"] == "MEDIO":
            dias_para_atender = 21 + i * 3
        else:
            dias_para_atender = 45 + i * 4
        fecha_sugerida = fecha_base + timedelta(days=dias_para_atender)
        cronograma.append({
            "cod": r["cod"],
            "nombre": r["nombre"],
            "nivel": r["nivel_riesgo"],
            "prob": r["prob_falla"],
            "fecha": fecha_sugerida.strftime("%d/%m/%Y"),
            "dias": dias_para_atender,
            "prioridad": i + 1
        })
    return cronograma


# ============================================================
#  SIMULADOR "QUE PASARIA SI" (WHAT-IF)
# ============================================================
# Se entrena el modelo una vez y se guarda para reutilizarlo
_simulador_modelo = None
_simulador_scaler = None

def _preparar_simulador(equipos, historial):
    """Entrena el modelo del simulador (una sola vez)."""
    global _simulador_modelo, _simulador_scaler
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    df = construir_caracteristicas(equipos, historial)
    df["riesgo"] = ((df["frec_fallas"] > df["frec_fallas"].median()) & (df["dias_ultima_falla"] > 25)).astype(int)
    X = df[["frec_fallas","dias_ultima_falla","antiguedad","indice_crit","costo_prom"]].values
    y = df["riesgo"].values
    _simulador_scaler = StandardScaler()
    Xs = _simulador_scaler.fit_transform(X)
    _simulador_modelo = LogisticRegression(max_iter=1000)
    _simulador_modelo.fit(Xs, y)

def predecir_personalizado(equipos, historial, frec_fallas, dias_ultima_falla, antiguedad, indice_crit, costo_prom):
    """
    Predice la probabilidad de falla para un conjunto de valores personalizados.
    Se usa en el simulador what-if.
    """
    global _simulador_modelo, _simulador_scaler
    if _simulador_modelo is None:
        _preparar_simulador(equipos, historial)
    X = [[frec_fallas, dias_ultima_falla, antiguedad, indice_crit, costo_prom]]
    Xs = _simulador_scaler.transform(X)
    prob = _simulador_modelo.predict_proba(Xs)[0][1] * 100
    nivel = "ALTO" if prob >= 70 else ("MEDIO" if prob >= 40 else "BAJO")
    return round(prob, 1), nivel

def valores_equipo(prediccion_df, codigo):
    """Devuelve los valores actuales de un equipo para inicializar el simulador."""
    fila = prediccion_df[prediccion_df["cod"]==codigo]
    if len(fila) == 0:
        return None
    r = fila.iloc[0]
    return {
        "frec_fallas": float(r["frec_fallas"]),
        "dias_ultima_falla": int(r["dias_ultima_falla"]),
        "antiguedad": int(r["antiguedad"]),
        "indice_crit": int(r["indice_crit"]),
        "costo_prom": float(r["costo_prom"]),
        "prob_actual": float(r["prob_falla"])
    }
