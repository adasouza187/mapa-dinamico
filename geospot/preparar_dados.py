"""
GeoSpot - Preparação de dados (roda uma vez)
CAMADA DE DADOS: lê o mapa dos distritos de SP e os CSVs do Censo 2022 (IBGE).
CAMADA DE CÁLCULO: monta os indicadores e salva um arquivo leve para o mapa.
Requisitos: pip install geopandas pandas
"""
import os
import pandas as pd
import geopandas as gpd

BASE = r"C:\Mapa dinamico"
SHP = os.path.join(BASE, "SP_distritos", "SP_distritos_CD2022.shp")
SAIDA = os.path.join(BASE, "geospot", "dados", "sp_distritos.geojson")

# ---------------- CAMADA DE DADOS ----------------
def ler_csv(nome):
    """Lê o CSV do IBGE (separador ';' e acentos em latin1) e mantém só SP (código 35)."""
    df = pd.read_csv(os.path.join(BASE, nome), sep=";", encoding="latin1", dtype=str)
    df.columns = [c.upper() for c in df.columns]
    return df[df["CD_DIST"].str.startswith("35")].copy()

def num(serie):
    """Converte texto em número: '.' vira vazio e a vírgula vira ponto decimal."""
    serie = serie.where(serie != ".")
    return pd.to_numeric(serie.str.replace(",", ".", regex=False), errors="coerce")

basico = ler_csv("Agregados_por_distritos_basico_BR.csv")
demo   = ler_csv("Agregados_por_distritos_demografia_BR.csv")
renda  = ler_csv("Agregados_por_distritos_renda_responsavel_BR.csv")

mapa = gpd.read_file(SHP)
mapa["CD_DIST"] = mapa["CD_DIST"].astype(str)
mapa = mapa[["CD_DIST", "geometry"]].to_crs(4326)                 # padrão de GPS (lat/long)
mapa["geometry"] = mapa.simplify(0.0003, preserve_topology=True)  # arquivo mais leve

# ---------------- CAMADA DE CÁLCULO ----------------
t = pd.DataFrame({"CD_DIST": basico["CD_DIST"]})
t["nome"]      = basico["NM_DIST"].values
t["municipio"] = basico["NM_MUN"].values
t["pop"]       = num(basico["V0001"]).values
t["area_km2"]  = num(basico["AREA_KM2"]).values
t["domicilios"] = num(basico["V0007"]).values
t["dens"] = (t["pop"] / t["area_km2"]).round(0)

r = pd.DataFrame({"CD_DIST": renda["CD_DIST"],
                  "renda_media": num(renda["V06004"]),
                  "renda_mediana": num(renda["V06006"])})
t = t.merge(r, on="CD_DIST", how="left")

# Demografia: 11 faixas para homens (V01009-19), mulheres (V01020-30) e total (V01031-41)
cols = [f"V{n:05d}" for n in range(1009, 1042)]
for c in cols:
    demo[c] = num(demo[c])
d = pd.DataFrame({"CD_DIST": demo["CD_DIST"]})
d["homens"]   = demo[cols[0:11]].fillna(0).astype(int).astype(str).agg(",".join, axis=1)
d["mulheres"] = demo[cols[11:22]].fillna(0).astype(int).astype(str).agg(",".join, axis=1)
d["pct_60"] = ((demo["V01040"] + demo["V01041"]) / num(demo["V01006"]) * 100).round(1)
t = t.merge(d, on="CD_DIST", how="left")

# Índice de Público (0-100): média da posição percentual em densidade e em renda
t["indice_publico"] = ((t["dens"].rank(pct=True) + t["renda_media"].rank(pct=True)) / 2 * 100).round(0)

saida = mapa.merge(t, on="CD_DIST", how="left")
os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
saida.to_file(SAIDA, driver="GeoJSON")
print(f"OK: {len(saida)} distritos salvos em {SAIDA}")
