import os, glob, json
import io
import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------- Ícones (Lucide, SVG) ----------
_SVG = {
    "map": '<polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/>',
    "pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "money": '<rect width="20" height="12" x="2" y="6" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M6 12h.01M18 12h.01"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "trophy": '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/>',
    "star": '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
    "scale": '<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10M12 3v18M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4M12 17h.01"/>',
    "sliders": '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/>',
    "layers": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "check": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
    "x": '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6M9 9l6 6"/>',
}
def ico(nome, cor="#7bd389", tam=20):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{tam}" height="{tam}" viewBox="0 0 24 24" '
            f'fill="none" stroke="{cor}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
            f'style="vertical-align:middle">{_SVG[nome]}</svg>')

def badge(nome, cor):  # ícone dentro de um quadrado com brilho
    return (f'<div class="ib" style="background:{cor}22;border:1px solid {cor}55;'
            f'box-shadow:0 0 18px {cor}33">{ico(nome, cor, 22)}</div>')

def secao(nome, titulo):  # título de seção da barra lateral
    st.sidebar.markdown(f'<div class="sec">{ico(nome, "#9a9ab5", 16)}<span>{titulo}</span></div>',
                        unsafe_allow_html=True)


st.set_page_config(page_title="Público-alvo SP – Censo 2022", page_icon=":material/map:", layout="wide")

# ---------- Visual ----------
st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#0f0c29,#16162b 50%,#0f1f33);}
[data-testid="stSidebar"]{background:#12121f;border-right:1px solid #2a2a40;}
h1,h2,h3{color:#fff;font-weight:700;}
.card{background:rgba(255,255,255,.05);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.1);
      border-radius:18px;padding:18px 20px;margin-bottom:14px;transition:.25s;height:100%;}
.card:hover{transform:translateY(-4px);box-shadow:0 10px 30px rgba(26,152,80,.35);}
.card p{color:#d8d8e8;margin:6px 0;line-height:1.5;}
.kpi{display:flex;flex-direction:column;}
.kpi .lbl{color:#9a9ab5;font-size:13px;text-transform:uppercase;letter-spacing:.5px;}
.kpi .val{color:#fff;font-size:30px;font-weight:800;}
.kpi .sub{color:#7bd389;font-size:13px;}
.nota{font-size:56px;font-weight:800;background:linear-gradient(90deg,#fdae61,#1a9850);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1;}
.nota span{font-size:20px;}
.tag{display:inline-block;padding:3px 12px;border-radius:20px;font-weight:600;font-size:13px;}
.ib{width:44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center;margin-bottom:12px;}
.card h3{display:flex;align-items:center;gap:10px;font-size:18px;margin:0 0 8px;}
.card h3 .ib{margin:0;}
.row{display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.06);color:#d8d8e8;}
.row:last-child{border-bottom:none;}
.row b{margin-left:auto;color:#fff;}
/* Barra lateral */
[data-testid="stSidebar"] .block-container{padding:1.5rem 1.2rem;}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.6rem;}
.sec{display:flex;align-items:center;gap:8px;margin:22px 0 4px;padding-bottom:8px;
     border-bottom:1px solid #2a2a40;color:#9a9ab5;font-size:12px;font-weight:700;
     text-transform:uppercase;letter-spacing:1px;}
.brand{display:flex;align-items:center;gap:10px;font-size:20px;font-weight:800;color:#fff;margin-bottom:6px;}
.brand .ib{margin:0;}
.formula{background:rgba(255,255,255,.04);border-left:3px solid #1a9850;border-radius:8px;
         padding:10px 12px;font-size:12px;color:#9a9ab5;line-height:1.5;}
.titulo{display:flex;align-items:center;gap:12px;color:#fff;font-weight:700;}
.titulo .ib{margin:0;}
/* Botão Exportar */
[data-testid="stDownloadButton"]{display:flex;justify-content:flex-end;margin-top:14px;}
[data-testid="stDownloadButton"] button{
  background:linear-gradient(135deg,#a8e6cf,#88c9e8);color:#0f1f33;border:none;
  border-radius:12px;padding:8px 20px;font-weight:700;
  box-shadow:0 4px 14px rgba(136,201,232,.25);transition:.25s;}
[data-testid="stDownloadButton"] button:hover{
  background:linear-gradient(135deg,#b9f0da,#a0d8f0);color:#0f1f33;
  transform:translateY(-2px);box-shadow:0 8px 22px rgba(136,201,232,.4);}
[data-testid="stDownloadButton"] button:focus{color:#0f1f33;box-shadow:none;}
</style>""", unsafe_allow_html=True)

BASE = os.path.dirname(os.path.abspath(__file__))

SP = "3550308"
FAIXA_20_49 = ["V01035", "V01036", "V01037", "V01038"]
TODAS_IDADES = [f"V010{i}" for i in range(31, 42)]

def ler(nome):
    arq = glob.glob(os.path.join(BASE, nome + ".*"))[0]
    if arq.endswith(".csv"):
        return pd.read_csv(arq, sep=";", dtype=str, encoding="latin-1")
    return pd.read_excel(arq, dtype=str)

def num(s):
    return pd.to_numeric(s.astype(str).str.replace(",", "."), errors="coerce")

# ---------- Dados ----------
@st.cache_resource(show_spinner="Carregando dados...")
def carregar():
    cache = os.path.join(BASE, "cache_sp.parquet")
    cache_geo = os.path.join(BASE, "cache_sp.geojson")
    if os.path.exists(cache) and os.path.exists(cache_geo):
        with open(cache_geo, encoding="utf-8") as f:
            return pd.read_parquet(cache), json.load(f)

    shp = glob.glob(os.path.join(BASE, "SP_distritos", "**", "*.shp"), recursive=True)[0]
    gdf = gpd.read_file(shp).to_crs(4326)
    gdf["CD_DIST"] = gdf["CD_DIST"].astype(str).str.strip()
    gdf = gdf[gdf["CD_DIST"].str.startswith(SP)].copy()
    gdf["geometry"] = gdf.geometry.simplify(0.0005, preserve_topology=True)

    renda = ler("Agregados_por_distritos_renda_responsavel_BR")
    renda["CD_DIST"] = renda["CD_DIST"].str.strip()
    renda = renda[renda.CD_DIST.str.startswith(SP)]
    renda["Renda"] = num(renda["V06004"])

    demo = ler("Agregados_por_distritos_demografia_BR")
    demo["CD_DIST"] = demo["CD_DIST"].str.strip()
    demo = demo[demo.CD_DIST.str.startswith(SP)].copy()
    for c in TODAS_IDADES:
        demo[c] = num(demo[c])
    demo["Populacao"] = demo[TODAS_IDADES].sum(axis=1)
    demo["Pop_20_49"] = demo[FAIXA_20_49].sum(axis=1)

    m = (gdf.merge(renda[["CD_DIST", "Renda"]], on="CD_DIST", how="left")
            .merge(demo[["CD_DIST", "Populacao", "Pop_20_49"]], on="CD_DIST", how="left"))
    m = m.rename(columns={"NM_DIST": "Distrito"})
    m["Prop_20_49"] = (m["Pop_20_49"] / m["Populacao"].replace(0, pd.NA) * 100).astype(float)

    geojson = json.loads(m[["CD_DIST", "geometry"]].to_json(drop_id=True))
    df = pd.DataFrame(m.drop(columns="geometry"))[["CD_DIST", "Distrito", "Renda", "Populacao", "Pop_20_49", "Prop_20_49"]]
    df.to_parquet(cache)
    with open(cache_geo, "w", encoding="utf-8") as f:
        json.dump(geojson, f)
    return df, geojson

dados, geojson = carregar()
dados = dados.copy()

def brl(v): return f"R$ {v:,.0f}".replace(",", ".")
def mil(v): return f"{v:,.0f}".replace(",", ".")
def norm(s): return (s - s.min()) / (s.max() - s.min()) * 100

# ---------- Painel lateral ----------
st.sidebar.markdown(f'<div class="brand">{badge("map", "#1a9850")}Público-alvo SP</div>', unsafe_allow_html=True)

secao("layers", "Cenário")
cenario = st.sidebar.radio("Cenário", ["Premium", "Popular"], horizontal=True, label_visibility="collapsed")

secao("money", "Faixas de renda")
p75, p50 = dados.Renda.quantile(.75), dados.Renda.median()
corte_prem = st.sidebar.slider("Premium: renda mínima (R$)", 1000.0, float(dados.Renda.max()), float(p75), 100.0)
corte_pop = st.sidebar.slider("Popular: renda máxima (R$)", 1000.0, float(dados.Renda.max()), float(p50), 100.0)

secao("sliders", "Pesos da nota")
w_r = st.sidebar.slider("Renda", 0, 100, 40)
w_v = st.sidebar.slider("Quantidade de pessoas 20–49", 0, 100, 30)
w_p = st.sidebar.slider("% da população com 20–49", 0, 100, 30)
soma = max(w_r + w_v + w_p, 1)

# ---------- Nota 0–100 ----------
dados["N_Renda"] = norm(dados.Renda) if cenario == "Premium" else 100 - norm(dados.Renda)
dados["N_Volume"] = norm(dados.Pop_20_49)
dados["N_Prop"] = norm(dados.Prop_20_49)
dados["Nota"] = ((w_r * dados.N_Renda + w_v * dados.N_Volume + w_p * dados.N_Prop) / soma).round(0)

def faixa(n):
    return "Excelente" if n >= 75 else "Boa" if n >= 50 else "Regular" if n >= 25 else "Fraca"
CORES = {"Excelente": "#1a9850", "Boa": "#91cf60", "Regular": "#fdae61", "Fraca": "#d73027"}
dados["Avaliacao"] = dados.Nota.apply(faixa)

dados["Premium"] = dados.Renda >= corte_prem
dados["Popular"] = dados.Renda <= corte_pop
dados["No cenário"] = dados[cenario].map({True: "Sim", False: "Não"})
alvo = dados[dados[cenario]]

st.sidebar.markdown(f"""<div class="formula">Nota = ({w_r}×Renda + {w_v}×Quantidade + {w_p}×Proporção) ÷ {soma}.<br>
Cada item vai de 0 (pior distrito) a 100 (melhor). {"Renda maior soma pontos." if cenario == "Premium"
else "Renda menor soma pontos."}</div>""", unsafe_allow_html=True)

secao("search", "Distrito")
sel = st.sidebar.selectbox("Distrito", sorted(dados.Distrito), index=None,
                           placeholder="Todos os distritos", label_visibility="collapsed")
d = dados[dados.Distrito == sel].iloc[0] if sel else None

if d is not None:
    pos = int((dados.Nota > d.Nota).sum() + 1)
    cor = CORES[d.Avaliacao]
    dentro = d[cenario]
    st.sidebar.markdown(f"""
<div class="card"><h3>{badge("pin", cor)}{d.Distrito}</h3>
<div class="nota">{d.Nota:.0f}<span>/100</span></div>
<span class="tag" style="background:{cor};color:#000">{d.Avaliacao}</span>
<div style="margin-top:12px">
<div class="row">{ico("trophy", "#f9c80e", 16)}Posição<b>{pos}º de {len(dados)}</b></div>
<div class="row">{ico("money", "#7bd389", 16)}Renda média<b>{brl(d.Renda)}</b></div>
<div class="row">{ico("users", "#4cc9f0", 16)}Moradores<b>{mil(d.Populacao)}</b></div>
<div class="row">{ico("target", "#f72585", 16)}20 a 49 anos<b>{mil(d.Pop_20_49)} ({d.Prop_20_49:.1f}%)</b></div>
<div class="row">{ico("check" if dentro else "x", "#1a9850" if dentro else "#d73027", 16)}
{"Faz parte" if dentro else "Fora"} do cenário</div>
</div></div>""", unsafe_allow_html=True)

# ---------- Exportar Excel (definido ANTES do cabeçalho) ----------
def gerar_excel():
    nomes = {"Avaliacao": "Avaliação", "Renda": "Renda média (R$)", "Populacao": "Moradores",
             "Pop_20_49": "Pessoas 20-49", "Prop_20_49": "% 20-49"}
    rank = (dados.sort_values("Nota", ascending=False)
            [["Distrito", "Nota", "Avaliacao", "Renda", "Populacao", "Pop_20_49", "Prop_20_49", "No cenário"]]
            .rename(columns=nomes))
    ricos = dados[dados.Premium & (dados.Prop_20_49 < dados.Prop_20_49.median())]
    ricos = ricos[["Distrito", "Nota", "Renda", "Pop_20_49", "Prop_20_49"]].rename(columns=nomes)
    params = pd.DataFrame({"Parâmetro": ["Cenário", "Renda mín. Premium", "Renda máx. Popular",
                                         "Peso Renda", "Peso Quantidade", "Peso Proporção"],
                           "Valor": [cenario, corte_prem, corte_pop, w_r, w_v, w_p]})
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for nome, df_ in [("Ranking", rank), ("Ricos com público velho", ricos), ("Parâmetros", params)]:
            df_.to_excel(xw, sheet_name=nome, index=False)
            ws = xw.sheets[nome]
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = max(len(str(c.value or "")) for c in col) + 3
    return buf.getvalue()

# ---------- Cabeçalho (título à esquerda, exportar à direita) ----------
h1, h2 = st.columns([5, 1], vertical_alignment="center")
with h1:
    st.markdown(f'<h1 class="titulo">{badge("map", "#1a9850")}Onde está o público – Cenário {cenario}</h1>',
                unsafe_allow_html=True)
with h2:
    st.download_button("Exportar Excel", data=gerar_excel(),
                       file_name=f"publico_alvo_sp_{cenario.lower()}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       icon=":material/download:")
st.caption("Fonte: Censo 2022 (IBGE). Cada distrito recebe uma nota de 0 a 100 conforme os pesos escolhidos na barra lateral.")

# ---------- KPIs ----------
melhor = dados.loc[dados.Nota.idxmax()]
kpis = [("map", "#4cc9f0", "Distritos no cenário", f"{len(alvo)} de {len(dados)}",
         f"renda {'≥' if cenario == 'Premium' else '≤'} {brl(corte_prem if cenario == 'Premium' else corte_pop)}"),
        ("users", "#f72585", "Público-alvo no cenário", mil(alvo.Pop_20_49.sum()), "pessoas de 20 a 49 anos"),
        ("trophy", "#f9c80e", "Melhor nota", f"{melhor.Nota:.0f}/100", melhor.Distrito),
        ("star", "#1a9850", "Notas acima de 75", str((dados.Nota >= 75).sum()), "distritos excelentes")]
for col, (i, cor, l, v, s) in zip(st.columns(4), kpis):
    col.markdown(f'<div class="card kpi">{badge(i, cor)}<div class="lbl">{l}</div>'
                 f'<div class="val">{v}</div><div class="sub">{s}</div></div>', unsafe_allow_html=True)

# ---------- Mapa de calor ----------
fig = px.choropleth(
    dados, geojson=geojson, locations="CD_DIST", featureidkey="properties.CD_DIST",
    color="Nota", range_color=(0, 100), color_continuous_scale="RdYlGn",
    hover_name="Distrito",
    hover_data={"Nota": ":.0f", "Avaliacao": True, "Renda": ":,.0f", "Pop_20_49": ":,.0f",
                "Prop_20_49": ":.1f", "No cenário": True, "CD_DIST": False},
    labels={"Avaliacao": "Avaliação", "Renda": "Renda (R$)", "Pop_20_49": "Pessoas 20–49",
            "Prop_20_49": "% 20–49"})
fig.update_traces(marker_line_color="#0f0c29", marker_line_width=0.6)

if d is not None:
    fig.add_trace(go.Choropleth(
        geojson=geojson, locations=[d.CD_DIST], featureidkey="properties.CD_DIST", z=[1],
        colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
        marker_line_color="#ffffff", marker_line_width=3.5, showscale=False, hoverinfo="skip"))

fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
fig.update_layout(height=650, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
                  font_color="#ddd",
                  coloraxis_colorbar=dict(title="Nota", tickvals=[0, 25, 50, 75, 100], thickness=14, len=.7))
st.plotly_chart(fig, use_container_width=True)

# ---------- Gráficos ----------
TEMA = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#ddd", height=450)
c1, c2 = st.columns(2)
with c1:
    top = dados.nlargest(10, "Nota").iloc[::-1]
    fb = px.bar(top, x="Nota", y="Distrito", orientation="h", color="Nota", range_color=(0, 100),
                color_continuous_scale="RdYlGn", text=top.Nota.map(lambda v: f"{v:.0f}"))
    fb.update_layout(title="Os 10 distritos com maior nota", yaxis_title=None,
                     coloraxis_showscale=False, xaxis_range=[0, 100], **TEMA)
    st.plotly_chart(fb, use_container_width=True)
with c2:
    fs = px.scatter(dados, x="Renda", y="Prop_20_49", size="Pop_20_49", color="Nota",
                    range_color=(0, 100), color_continuous_scale="RdYlGn", hover_name="Distrito", size_max=40,
                    labels={"Prop_20_49": "% de moradores com 20–49 anos", "Renda": "Renda média (R$)"})
    if d is not None:
        fs.add_trace(go.Scatter(x=[d.Renda], y=[d.Prop_20_49], mode="markers+text", text=[d.Distrito],
                                textposition="top center", showlegend=False, textfont_color="#fff",
                                marker=dict(size=22, color="rgba(0,0,0,0)", line=dict(color="#fff", width=3))))
    fs.update_layout(title="Renda x público jovem (bolha maior = mais pessoas)", **TEMA)
    st.plotly_chart(fs, use_container_width=True)

# ---------- O que os dados dizem ----------
st.markdown(f'<h2 class="titulo">{badge("target", "#f72585")}O que os dados dizem</h2>',
            unsafe_allow_html=True)
prem, popu = dados[dados.Premium], dados[dados.Popular]
g = prem if cenario == "Premium" else popu

# 1. Concentração
t5 = g.nlargest(5, "Pop_20_49")
share = t5.Pop_20_49.sum() / g.Pop_20_49.sum() * 100 if len(g) else 0
# 2. Comparativo
raz = prem.Renda.mean() / popu.Renda.mean()
raz_pop = popu.Populacao.mean() / prem.Populacao.mean()
# 3. Renda alta
corr = dados[["Renda", "Prop_20_49"]].corr().iloc[0, 1]
forca = ("praticamente nenhuma" if abs(corr) < .2 else "fraca" if abs(corr) < .4
         else "moderada" if abs(corr) < .7 else "forte")
med = dados.Prop_20_49.median()
fracos = prem[prem.Prop_20_49 < med].sort_values("Renda", ascending=False)

a, b, c = st.columns(3)

a.markdown(f"""<div class="card"><h3>{badge("target", "#4cc9f0")}Onde está o público</h3>
<p>No cenário <b>{cenario}</b> há <b>{mil(g.Pop_20_49.sum())} pessoas</b> de 20 a 49 anos espalhadas
por <b>{len(g)} distritos</b>.</p>
<p>Só 5 deles, <b>{', '.join(t5.Distrito)}</b>, reúnem <b>{share:.0f}%</b> desse público.
É por eles que vale começar.</p></div>""", unsafe_allow_html=True)

b.markdown(f"""<div class="card"><h3>{badge("scale", "#a78bfa")}Premium e Popular são iguais?</h3>
<p><b>Não.</b> Nos distritos Premium a renda média é de <b>{brl(prem.Renda.mean())}</b>,
<b>{raz:.1f} vezes</b> a dos distritos Popular (<b>{brl(popu.Renda.mean())}</b>).</p>
<p>Os distritos Popular são <b>{raz_pop:.1f} vezes mais populosos</b>. A parte de jovens adultos é quase igual:
{prem.Prop_20_49.mean():.1f}% no Premium contra {popu.Prop_20_49.mean():.1f}% no Popular.
A diferença está no dinheiro e no tamanho, não na idade.</p></div>""", unsafe_allow_html=True)

c.markdown(f"""<div class="card"><h3>{badge("alert", "#fdae61")}Renda alta é sempre melhor?</h3>
<p><b>Não.</b> A relação entre ser rico e ter muitos jovens adultos é <b>{forca}</b>
(índice {corr:.2f}, numa escala de -1 a 1).</p>
<p>Dos <b>{len(prem)}</b> distritos ricos, <b>{len(fracos)}</b> têm menos jovens adultos que a média da
cidade ({med:.1f}%). Por exemplo, <b>{', '.join(fracos.Distrito.head(3))}</b>. Há dinheiro, mas o público
é mais velho.</p></div>""", unsafe_allow_html=True)

# ---------- Tabelas ----------
COLS = {
    "Nota": st.column_config.ProgressColumn("Nota", min_value=0, max_value=100, format="%d"),
    "Avaliacao": "Avaliação",
    "Renda": st.column_config.NumberColumn("Renda média", format="R$ %.0f"),
    "Pop_20_49": st.column_config.NumberColumn("Pessoas de 20 a 49 anos", format="%d"),
    "Prop_20_49": st.column_config.NumberColumn("% de 20 a 49 anos", format="%.1f%%"),
    "No cenário": "No cenário?"}

tab1, tab2 = st.tabs(["Ranking completo", "Distritos ricos com público mais velho"])
with tab1:
    st.dataframe(dados.sort_values("Nota", ascending=False)
                 [["Distrito", "Nota", "Avaliacao", "Renda", "Pop_20_49", "Prop_20_49", "No cenário"]],
                 hide_index=True, use_container_width=True, column_config=COLS, height=420)
with tab2:
    st.dataframe(fracos[["Distrito", "Nota", "Renda", "Pop_20_49", "Prop_20_49"]],
                 hide_index=True, use_container_width=True, column_config=COLS)

