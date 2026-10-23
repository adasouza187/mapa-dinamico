import os, glob, json
import geopandas as gpd
import pandas as pd
import plotly.express as px

BASE = r"C:\Mapa dinamico"
CSV_PATH = os.path.join(BASE, "Agregados_por_distritos_renda_responsavel_BR.xlsx")

# 1. Malha (shapefile de distritos)
shp = glob.glob(os.path.join(BASE, "**", "*.shp"), recursive=True)
print("Shapefiles encontrados:", shp)
gdf = gpd.read_file(shp[0]).to_crs(4326)
gdf["CD_DIST"] = gdf["CD_DIST"].astype(str).str.strip()
gdf = gdf[gdf["CD_DIST"].str.startswith("3550308")].reset_index(drop=True)
print("Distritos SP na malha:", len(gdf))

# 2. Dados
df = pd.read_excel(CSV_PATH, dtype=str)
df["CD_DIST"] = df["CD_DIST"].str.strip()
df = df[df["CD_DIST"].str.startswith("3550308")]
print("Distritos SP no arquivo:", len(df))

df["V06004"] = pd.to_numeric(df["V06004"].str.replace(",", "."), errors="coerce")

mapa = gdf.merge(df[["CD_DIST", "V06004"]], on="CD_DIST", how="left")
print("Sem renda:", mapa["V06004"].isna().sum())

# 3. Mapa interativo
geojson = json.loads(mapa[["CD_DIST", "geometry"]].to_json())

fig = px.choropleth(
    mapa, geojson=geojson,
    locations="CD_DIST", featureidkey="properties.CD_DIST",
    color="V06004", color_continuous_scale="Viridis",
    hover_name="NM_DIST",
    hover_data={"V06004": ":,.2f", "CD_DIST": False},
    labels={"V06004": "Renda média (R$)"})
fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(margin=dict(l=0, r=0, t=40, b=0),
                  title="Renda média por distrito – São Paulo (Censo 2022)")
fig.write_html(os.path.join(BASE, "mapa_renda.html"), include_plotlyjs="cdn")
print("Gerado: mapa_renda.html")
