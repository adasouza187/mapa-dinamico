"""Filtra SP (3550308) na malha de distritos, confere com sp_renda.csv e plota contornos"""
import glob, os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

BASE = r"C:\Mapa dinamico"
COD = "3550308"

# 1. Localiza a malha (shapefile ou GeoJSON)
arqs = [a for ext in ("*.shp", "*.geojson", "*.json", "*.gpkg")
        for a in glob.glob(os.path.join(BASE, "**", ext), recursive=True)]
if not arqs:
    raise SystemExit("Nenhuma malha encontrada em " + BASE)
print("Malha:", arqs[0])

gdf = gpd.read_file(arqs[0])
gdf.columns = [c.upper() if c != "geometry" else c for c in gdf.columns]
gdf["CD_DIST"] = gdf["CD_DIST"].astype(str).str.strip()
sp = gdf[gdf["CD_DIST"].str[:7] == COD].copy()

# 2. Contagem
print(f"\n1) Polígonos encontrados: {len(sp)}")
print(f"   CD_DIST únicos: {sp['CD_DIST'].nunique()}")
multi = (sp.geometry.geom_type == "MultiPolygon").sum()
print(f"   MultiPolygon: {multi} | inválidos: {(~sp.is_valid).sum()}")

# 3. Comparação com o CSV
csv = pd.read_csv(os.path.join(BASE, "sp_renda.csv"), sep=";", dtype={"CD_DIST": str})
cod_csv, cod_malha = set(csv["CD_DIST"].str.strip()), set(sp["CD_DIST"])
print(f"\n2) Distritos no CSV: {len(cod_csv)}")
print(f"   Em comum: {len(cod_csv & cod_malha)}")
print(f"   Só no CSV:   {sorted(cod_csv - cod_malha) or 'nenhum'}")
print(f"   Só na malha: {sorted(cod_malha - cod_csv) or 'nenhum'}")

# 4. Apenas contornos, em cinza
fig, ax = plt.subplots(figsize=(8, 11))
sp.boundary.plot(ax=ax, color="gray", linewidth=0.6)
ax.set_axis_off()
ax.set_title("Município de São Paulo – distritos (contornos)", color="gray")
out = os.path.join(BASE, "contornos_sp.png")
plt.savefig(out, dpi=150, bbox_inches="tight")
print(f"\nImagem salva: {out}")
plt.show()
