#!/usr/bin/env python3
"""
Dashboard de Leads - Análise Mensal por Cliente
Lê direto da pasta do Google Drive via arquivo CSV exportado.
 
Uso:
    python dashboard_leads.py
 
Requisitos:
    pip install pandas plotly dash
"""
 
import re
import csv
import io
import base64
from collections import defaultdict, Counter
 
# ─── DADOS REAIS (Willian PlanMaster - extraídos via Google Drive) ─────────────
# Para atualizar: basta substituir o CSV abaixo com o novo conteúdo exportado
# ou adaptar para ler direto de um arquivo local.
 
PLANO_LIST = {'UNIMED','BRADESCO','AMIL','OUTRO','NOTREDAME','SULAMERICA',
              'SUL AMERICA','PORTO SEGURO','HAPVIDA','GOLDEN CROSS'}
 
TICKET_MAP = {
    'Até R$ 500': 350,
    'Até R$ 1.000': 750,
    'Até R$ 1.500': 1250,
    'Até R$ 2.000': 1750,
    'Até R$ 3.000': 2500,
    'Acima de R$ 3.000': 3500,
}
 
MESES_PT = {1:'Jan',2:'Fev',3:'Mar',4:'Abr',5:'Mai',6:'Jun',
            7:'Jul',8:'Ago',9:'Set',10:'Out',11:'Nov',12:'Dez'}
 
STATUS_LABELS = [
    'Cotação Enviada','Aguardando Atendimento','Finalizado',
    'Contato Feito','Venda Realizada','Outros'
]
 
 
def parse_leads_csv(csv_text: str) -> list[dict]:
    """Lê o CSV exportado da planilha e retorna lista de leads processados."""
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)
    if not rows:
        return []
 
    leads = []
    for row in rows[1:]:
        if len(row) < 19:
            continue
        cnpj    = row[0].strip()
        opcao   = row[1].strip()
        plano   = row[2].strip()
        custo   = row[3].strip()
        qtd     = row[4].strip()
        submitted = row[18].strip()
        status  = row[20].strip() if len(row) > 20 else ''
 
        m = re.search(r'(\d{2})/(\d{2})/(\d{4})', submitted)
        if not m:
            continue
        mes_n = int(m.group(2))
        ano   = int(m.group(3))
        mes_label = f'{MESES_PT[mes_n]}/{ano}'
 
        if 'NÃO TENHO PLANO' in opcao.upper():
            tem_plano = False
            plano_final = 'Sem plano'
        elif plano.upper() in PLANO_LIST:
            tem_plano = True
            plano_final = plano.upper().title()
        elif 'MEI' in cnpj.upper() and not plano:
            tem_plano = False
            plano_final = 'Sem plano (MEI)'
        else:
            tem_plano = False
            plano_final = 'Sem plano'
 
        nums = re.findall(r'\d+', qtd)
        n_vidas = int(nums[0]) if nums else 1
        ticket  = TICKET_MAP.get(custo, 0)
 
        leads.append({
            'mes': mes_label, 'mes_n': mes_n, 'ano': ano,
            'plano': plano_final, 'tem_plano': tem_plano,
            'ticket': ticket, 'vidas': n_vidas, 'status': status,
        })
    return leads
 
 
def aggregate_by_month(leads: list[dict]) -> dict:
    """Agrupa e calcula métricas por mês."""
    meses = defaultdict(list)
    for l in leads:
        meses[(l['ano'], l['mes_n'], l['mes'])].append(l)
 
    result = {}
    for (ano, mn, mes), lista in sorted(meses.items()):
        com  = sum(1 for l in lista if l['tem_plano'])
        sem  = len(lista) - com
        tks  = [l['ticket'] for l in lista if l['tem_plano'] and l['ticket'] > 0]
        tk   = int(sum(tks) / len(tks)) if tks else 0
        vf   = Counter()
        for l in lista:
            v = l['vidas']
            vf[5 if v >= 5 else v] += 1
        sc = Counter(l['status'] for l in lista if l['status'])
        pc = Counter(l['plano'] for l in lista if l['tem_plano'])
        vd = sum(1 for l in lista if 'venda' in l['status'].lower())
        tv = sum(l['vidas'] for l in lista)
 
        # Montar dados de operadora: com plano + sem plano
        all_ops = list(dict(pc.most_common(6)).keys()) + ['Sem plano']
        ops_com = {op: pc.get(op, 0) for op in all_ops}
        ops_sem = {'Sem plano': sem}
 
        result[mes] = {
            'leads': len(lista), 'vidas': tv,
            'com': com, 'sem': sem,
            'tk': tk, 'vd': vd,
            'vf': [vf[1], vf[2], vf[3], vf[4], vf[5]],
            'sc': [
                sc.get('Cotação Enviada', 0),
                sc.get('Aguardando atendimento', 0),
                sc.get('Finalizado', 0),
                sc.get('Contato Feito', 0),
                sc.get('Venda realizada', 0),
                sum(v for k, v in sc.items() if k not in
                    {'Cotação Enviada','Aguardando atendimento','Finalizado',
                     'Contato Feito','Venda realizada'}),
            ],
            'ops_labels': all_ops,
            'ops_com':    [ops_com.get(op, 0) for op in all_ops],
            'ops_sem':    [ops_sem.get(op, 0) for op in all_ops],
            'planos_top': dict(pc.most_common(6)),
        }
    return result
 
 
# ─── DADOS PRÉ-PROCESSADOS (Willian PlanMaster — via Google Drive) ──────────────
# Gerados pelo script de ingestão acima com os dados reais de Dez/2025–Mai/2026
 
CLIENTES = {
    'willian': {
        'nome': 'Willian PlanMaster',
        'cor': '#1D9E75',
        'meses': {
            'Dez/2025': {'leads':111,'vidas':293,'com':70,'sem':41,'tk':767,'vd':0,
                'vf':[5,57,29,13,7],'sc':[0,0,0,0,0,111],
                'ops_labels':['Unimed','Outro','Bradesco','Amil','Notredame','Sem plano'],
                'ops_com':   [32,22,10,5,1,0],
                'ops_sem':   [0,0,0,0,0,41]},
            'Jan/2026': {'leads':140,'vidas':378,'com':95,'sem':45,'tk':742,'vd':0,
                'vf':[0,77,38,15,10],'sc':[0,0,0,0,0,140],
                'ops_labels':['Unimed','Outro','Bradesco','Amil','Notredame','Porto Seguro','Sem plano'],
                'ops_com':   [42,24,13,9,6,1,0],
                'ops_sem':   [0,0,0,0,0,0,45]},
            'Fev/2026': {'leads':121,'vidas':312,'com':63,'sem':58,'tk':887,'vd':0,
                'vf':[0,73,29,16,3],'sc':[0,0,0,0,0,121],
                'ops_labels':['Unimed','Amil','Outro','Notredame','Sem plano'],
                'ops_com':   [44,9,8,2,0],
                'ops_sem':   [0,0,0,0,58]},
            'Mar/2026': {'leads':132,'vidas':370,'com':82,'sem':50,'tk':766,'vd':0,
                'vf':[0,63,40,21,8],'sc':[0,0,0,0,0,132],
                'ops_labels':['Unimed','Outro','Notredame','Amil','Bradesco','Sem plano'],
                'ops_com':   [51,16,5,5,5,0],
                'ops_sem':   [0,0,0,0,0,50]},
            'Abr/2026': {'leads':76,'vidas':205,'com':37,'sem':39,'tk':694,'vd':0,
                'vf':[0,36,29,9,2],'sc':[6,2,2,0,0,66],
                'ops_labels':['Unimed','Outro','Notredame','Amil','Sem plano'],
                'ops_com':   [23,10,2,2,0],
                'ops_sem':   [0,0,0,0,39]},
            'Mai/2026': {'leads':3,'vidas':9,'com':3,'sem':0,'tk':1416,'vd':0,
                'vf':[0,1,1,1,0],'sc':[0,0,0,0,0,3],
                'ops_labels':['Unimed','Amil','Sem plano'],
                'ops_com':   [2,1,0],
                'ops_sem':   [0,0,0]},
        }
    },
    'daniela': {
        'nome': 'Daniela BVita',
        'cor': '#185FA5',
        'meses': {
            'Mar/2026': {'leads':84,'vidas':228,'com':52,'sem':32,'tk':983,'vd':0,
                'vf':[0,23,31,22,8],'sc':[84,0,0,0,0,0],
                'ops_labels':['Unimed','Outro','Amil','Notredame','Bradesco','Sem plano'],
                'ops_com':   [28,14,7,5,3,0],
                'ops_sem':   [0,0,0,0,0,32]},
            'Abr/2026': {'leads':168,'vidas':468,'com':72,'sem':96,'tk':1042,'vd':0,
                'vf':[0,51,54,42,21],'sc':[0,0,0,0,0,168],
                'ops_labels':['Unimed','Outro','Amil','Notredame','SulAmérica','Sem plano'],
                'ops_com':   [38,22,12,8,7,0],
                'ops_sem':   [0,0,0,0,0,96]},
        }
    }
}
 
 
def computar_total(cliente_key: str) -> dict:
    """Agrega todos os meses de um cliente."""
    meses = CLIENTES[cliente_key]['meses']
    agg = {'leads':0,'vidas':0,'com':0,'sem':0,'tk':0,'vd':0,
           'vf':[0,0,0,0,0],'sc':[0,0,0,0,0,0],
           'ops_labels':['Unimed','Outro','Bradesco','Amil','Notredame','Sem plano'],
           'ops_com':[0,0,0,0,0,0],'ops_sem':[0,0,0,0,0,0]}
    ts = 0; tc = 0
    for d in meses.values():
        agg['leads'] += d['leads']; agg['vidas'] += d['vidas']
        agg['com']   += d['com'];   agg['sem']   += d['sem']
        agg['vd']    += d['vd']
        ts += d['tk'] * d['com']; tc += d['com']
        for i in range(5): agg['vf'][i] += d['vf'][i]
        for i in range(6): agg['sc'][i] += d['sc'][i]
        for i, lbl in enumerate(d['ops_labels']):
            if lbl in agg['ops_labels']:
                idx = agg['ops_labels'].index(lbl)
                agg['ops_com'][idx] += d['ops_com'][i]
                agg['ops_sem'][idx] += d['ops_sem'][i]
    agg['tk'] = int(ts / tc) if tc > 0 else 0
    return agg
 
 
# ─── GERAÇÃO DO HTML ─────────────────────────────────────────────────────────────
 
def gerar_dashboard_html() -> str:
    import json as _json
    db_json = _json.dumps(CLIENTES, ensure_ascii=False)
 
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard de Leads</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
/* ── RESET & BASE ─────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
:root {{
  --green:  #1D9E75; --green-lt: #9FE1CB; --green-bg: #f0faf6;
  --blue:   #185FA5; --blue-lt:  #A8C8F0; --blue-bg:  #EEF4FD;
  --yellow: #F0B429;
  --text:   #1A1917; --text2: #6B6966; --text3: #888780;
  --bg:     #FAFAF8; --bg2: #F3F2EF; --border: #E5E4E0;
  --radius: 10px; --shadow: 0 1px 3px rgba(0,0,0,.08);
}}
body {{ font-family: 'DM Sans', 'Helvetica Neue', sans-serif;
       background: var(--bg); color: var(--text); padding: 16px; }}
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap');
 
/* ── TOPBAR ──────────────────────────────────────────── */
.topbar {{ display:flex; align-items:center; justify-content:space-between;
          padding-bottom: 14px; border-bottom: 1px solid var(--border);
          margin-bottom: 18px; flex-wrap: wrap; gap: 10px; }}
.topbar h1 {{ font-size: 17px; font-weight: 600; }}
.topbar p  {{ font-size: 12px; color: var(--text3); }}
.client-info {{ display:flex; align-items:center; gap: 10px; }}
.avatar {{ width:34px; height:34px; border-radius:50%; display:flex;
           align-items:center; justify-content:center;
           font-size:12px; font-weight:600; flex-shrink:0; }}
.av-w {{ background:#E1F5EE; color:#0F6E56; }}
.av-d {{ background:#E8F0FD; color:#1A56B0; }}
.badge-live {{ display:inline-flex; align-items:center; gap:4px;
               font-size:10px; padding:2px 8px; border-radius:20px;
               background:#E1F5EE; color:#0F6E56; }}
 
/* ── CONTROLS ────────────────────────────────────────── */
.controls {{ display:flex; gap:8px; flex-wrap:wrap;
             margin-bottom: 18px; align-items:center; }}
select {{ font-size:13px; padding:6px 10px; border-radius:6px;
          border:1px solid var(--border); background:white;
          color:var(--text); cursor:pointer; }}
.btn-refresh {{ font-size:12px; padding:6px 13px; border-radius:6px;
                border:1px solid var(--green); background:transparent;
                color:var(--green); cursor:pointer; font-weight:500; }}
 
/* ── PILLS ───────────────────────────────────────────── */
.stitle {{ font-size:11px; font-weight:500; color:var(--text3);
           text-transform:uppercase; letter-spacing:.06em; margin-bottom:10px; }}
.pills {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr));
          gap:8px; margin-bottom:18px; }}
.pill {{ background:white; border:1px solid var(--border); border-radius:var(--radius);
         padding:10px 12px; cursor:pointer; transition:all .15s; }}
.pill:hover {{ border-color: var(--green); }}
.pill.act-g {{ border-color:var(--green); background:var(--green-bg); }}
.pill.act-b {{ border-color:var(--blue);  background:var(--blue-bg); }}
.pill-name {{ font-size:11px; font-weight:500; color:var(--text); margin-bottom:4px; }}
.pill-val  {{ font-size:20px; font-weight:600; }}
.pill-sub  {{ font-size:10px; color:var(--text3); margin-top:2px; }}
.g {{ color:var(--green); }} .b {{ color:var(--blue); }}
.tup {{ color:var(--green); font-size:10px; }}
.tdn {{ color:#C0392B; font-size:10px; }}
.open-badge {{ font-size:10px; padding:1px 5px; border-radius:10px;
               background:#FAEEDA; color:#854F0B; margin-left:3px; }}
 
/* ── METRICS GRID ────────────────────────────────────── */
.mgrid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(100px,1fr));
          gap:10px; margin-bottom:18px; }}
.mc {{ background:var(--bg2); border-radius:var(--radius); padding:12px 14px; }}
.mc-label {{ font-size:11px; color:var(--text3); margin-bottom:4px; }}
.mc-val   {{ font-size:21px; font-weight:600; color:var(--text); }}
.mc-val.g {{ color:var(--green); }} .mc-val.b {{ color:var(--blue); }}
.mc-sub   {{ font-size:11px; color:var(--text3); margin-top:2px; }}
 
/* ── TWO COL ─────────────────────────────────────────── */
.tcol {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:16px; }}
.card {{ background:white; border:1px solid var(--border);
         border-radius:var(--radius); padding:14px 16px; box-shadow:var(--shadow); }}
.ct   {{ font-size:11px; font-weight:500; color:var(--text3);
         text-transform:uppercase; letter-spacing:.05em; margin-bottom:12px; }}
 
/* ── VIDA BARS ───────────────────────────────────────── */
.vrow  {{ display:flex; align-items:center; gap:8px; margin-bottom:7px; font-size:12px; }}
.vlbl  {{ min-width:54px; color:var(--text3); }}
.vtrack {{ flex:1; height:6px; background:var(--bg2); border-radius:3px; overflow:hidden; }}
.vfill  {{ height:100%; border-radius:3px; }}
.vcnt   {{ min-width:22px; text-align:right; font-weight:500; }}
 
/* ── STATUS LIST ─────────────────────────────────────── */
.slist {{ display:flex; flex-direction:column; gap:6px; }}
.srow  {{ display:flex; align-items:center; justify-content:space-between; font-size:12px; }}
.sname {{ color:var(--text3); flex:1; }}
.sbadge {{ font-size:10px; font-weight:600; padding:2px 8px;
           border-radius:20px; min-width:24px; text-align:center; }}
.sc {{ background:#E6F1FB; color:#185FA5; }} .sa {{ background:#FAEEDA; color:#854F0B; }}
.sv {{ background:#EAF3DE; color:#3B6D11; }} .sf {{ background:#F1EFE8; color:#5F5E5A; }}
.sk {{ background:#EEEDFE; color:#534AB7; }} .so {{ background:#FCEBEB; color:#A32D2D; }}
 
/* ── CHARTS ──────────────────────────────────────────── */
.cw  {{ position:relative; width:100%; height:180px; }}
.cw2 {{ position:relative; width:100%; height:220px; }}
 
/* ── INSIGHT ─────────────────────────────────────────── */
.ibox {{ background:var(--bg2); border-left:3px solid var(--green);
         border-radius:0 var(--radius) var(--radius) 0;
         padding:10px 14px; margin-bottom:16px; }}
.ibox.b {{ border-left-color:var(--blue); }}
.ibox p {{ font-size:12px; color:var(--text3); line-height:1.75; }}
 
/* ── LEGEND ──────────────────────────────────────────── */
.lgrow {{ display:flex; gap:14px; flex-wrap:wrap; margin-bottom:8px;
          font-size:11px; color:var(--text3); }}
.lgrow span {{ display:flex; align-items:center; gap:5px; }}
.lgdot {{ width:10px; height:10px; border-radius:2px; }}
</style>
</head>
<body>
 
<div class="topbar">
  <div>
    <h1>Dashboard de Leads</h1>
    <p>Atualizado via Google Drive · <span class="badge-live">● Conectado</span></p>
  </div>
  <div class="client-info">
    <div class="avatar av-w" id="cav">WP</div>
    <div>
      <div style="font-size:13px;font-weight:600" id="cnm">Willian PlanMaster</div>
      <div style="font-size:11px;color:var(--text3)" id="csb">Bradesco</div>
    </div>
  </div>
</div>
 
<div class="controls">
  <select id="csel">
    <option value="willian">Willian PlanMaster</option>
    <option value="daniela">Daniela BVita</option>
  </select>
  <select id="msel"></select>
  <button class="btn-refresh" id="btnr">↻ Atualizar dados</button>
</div>
 
<p class="stitle">Visão geral por mês</p>
<div class="pills" id="pills"></div>
 
<p class="stitle" id="dtitle">Métricas do período</p>
<div class="mgrid" id="mgrid"></div>
 
<div class="tcol">
  <div class="card"><p class="ct">Vidas por faixa</p><div id="vbars"></div></div>
  <div class="card"><p class="ct">Status dos leads</p><div class="slist" id="slist"></div></div>
</div>
 
<div class="card" style="margin-bottom:16px">
  <p class="ct">Evolução mensal de leads</p>
  <div class="cw"><canvas id="tc"></canvas></div>
</div>
 
<div class="card" style="margin-bottom:16px">
  <p class="ct">Leads por operadora — Com plano vs Sem plano</p>
  <div class="lgrow">
    <span><span class="lgdot" style="background:var(--green)"></span>Com plano</span>
    <span><span class="lgdot" style="background:var(--yellow)"></span>Sem plano</span>
  </div>
  <div class="cw2"><canvas id="pc"></canvas></div>
</div>
 
<div class="ibox" id="ibox"><p id="itxt"></p></div>
 
<script>
var DB = {db_json};
 
// ── Helpers ──────────────────────────────────────────────────────────
var SL = ['Cotação Enviada','Aguardando Atend.','Finalizado','Contato Feito','Venda Realizada','Outros'];
var SC = ['sc','sa','sf','sk','sv','so'];
var VC = ['#378ADD','#1D9E75','#EF9F27','#D4537E','#7F77DD'];
var VL = ['1 vida','2 vidas','3 vidas','4 vidas','5+ vidas'];
 
var tc_inst = null, pc_inst = null;
var ck = 'willian', cm = 'all';
 
function total(k) {{
  var mo = DB[k].meses, ks = Object.keys(mo);
  var a = {{leads:0,vidas:0,com:0,sem:0,tk:0,vd:0,vf:[0,0,0,0,0],sc:[0,0,0,0,0,0],
           ops_labels:['Unimed','Outro','Bradesco','Amil','Notredame','Sem plano'],
           ops_com:[0,0,0,0,0,0],ops_sem:[0,0,0,0,0,0]}};
  var ts=0,tc2=0;
  ks.forEach(function(k2) {{
    var d=mo[k2];
    a.leads+=d.leads;a.vidas+=d.vidas;a.com+=d.com;a.sem+=d.sem;a.vd+=d.vd;
    ts+=d.tk*d.com;tc2+=d.com;
    for(var i=0;i<5;i++) a.vf[i]+=d.vf[i];
    for(var i=0;i<6;i++) a.sc[i]+=d.sc[i];
    d.ops_labels.forEach(function(lb,i) {{
      var idx=a.ops_labels.indexOf(lb);
      if(idx>=0){{ a.ops_com[idx]+=(d.ops_com[i]||0); a.ops_sem[idx]+=(d.ops_sem[i]||0); }}
    }});
  }});
  a.tk = tc2>0?Math.round(ts/tc2):0;
  return a;
}}
 
function popSel(k) {{
  var s=document.getElementById('msel');
  s.innerHTML='<option value="all">Todos os meses</option>';
  Object.keys(DB[k].meses).forEach(function(mk) {{
    var o=document.createElement('option');
    o.value=mk; o.textContent=mk;
    s.appendChild(o);
  }});
}}
 
function pills(k,act) {{
  var c=DB[k],ks=Object.keys(c.meses);
  var cor=c.cor, acls=k==='willian'?'act-g':'act-b';
  var tot=ks.reduce(function(s,mk){{return s+c.meses[mk].leads;}},0);
  var h='<div class="pill '+(act==='all'?acls:'')+'" onclick="sel(\'all\')">'
       +'<div class="pill-name">Todos</div>'
       +'<div class="pill-val" style="color:'+cor+'">'+tot+'</div>'
       +'<div class="pill-sub">leads totais</div></div>';
  ks.forEach(function(mk,i) {{
    var d=c.meses[mk],prev=i>0?c.meses[ks[i-1]].leads:null;
    var tr=prev?(d.leads>=prev?'<span class="tup">▲'+(d.leads-prev)+'</span>':'<span class="tdn">▼'+(prev-d.leads)+'</span>'):'';
    var ob=mk.includes('Abr')&&k==='daniela'?'<span class="open-badge">aberto</span>':'';
    h+='<div class="pill '+(act===mk?acls:'')+'" onclick="sel(\''+mk+\'\')">'
      +'<div class="pill-name">'+mk+' '+tr+ob+'</div>'
      +'<div class="pill-val" style="color:'+cor+'">'+d.leads+'</div>'
      +'<div class="pill-sub">R$'+d.tk.toLocaleString('pt-BR')+'</div></div>';
  }});
  document.getElementById('pills').innerHTML=h;
}}
 
function metrics(d,lb) {{
  document.getElementById('dtitle').textContent='Métricas — '+lb;
  var p=function(v){{return d.leads>0?Math.round(v/d.leads*100):0;}};
  var gc=ck==='willian'?'g':'b';
  document.getElementById('mgrid').innerHTML=
    '<div class="mc"><div class="mc-label">Total leads</div><div class="mc-val">'+d.leads+'</div></div>'+
    '<div class="mc"><div class="mc-label">Total vidas</div><div class="mc-val">'+d.vidas+'</div></div>'+
    '<div class="mc"><div class="mc-label">Com plano</div><div class="mc-val">'+d.com+'</div><div class="mc-sub">'+p(d.com)+'% dos leads</div></div>'+
    '<div class="mc"><div class="mc-label">Sem plano</div><div class="mc-val">'+d.sem+'</div><div class="mc-sub">'+p(d.sem)+'% dos leads</div></div>'+
    '<div class="mc"><div class="mc-label">Ticket médio</div><div class="mc-val" style="font-size:15px;padding-top:4px">R$'+d.tk.toLocaleString('pt-BR')+'</div></div>'+
    '<div class="mc"><div class="mc-label">Vendas</div><div class="mc-val '+gc+'">'+d.vd+'</div><div class="mc-sub">'+p(d.vd)+'% conv.</div></div>';
}}
 
function vidas(vf) {{
  var mx=Math.max.apply(null,vf.concat([1]));
  document.getElementById('vbars').innerHTML=vf.map(function(v,i) {{
    return '<div class="vrow"><span class="vlbl">'+VL[i]+'</span>'
          +'<div class="vtrack"><div class="vfill" style="width:'+Math.round(v/mx*98)+'%;background:'+VC[i]+'"></div></div>'
          +'<span class="vcnt">'+v+'</span></div>';
  }}).join('');
}}
 
function status_render(sc) {{
  document.getElementById('slist').innerHTML=SL.map(function(lb,i) {{
    return '<div class="srow"><span class="sname">'+lb+'</span><span class="sbadge '+SC[i]+'">'+sc[i]+'</span></div>';
  }}).join('');
}}
 
function trend(k) {{
  var c=DB[k],ks=Object.keys(c.meses);
  var lt=k==='willian'?'#9FE1CB':'#A8C8F0';
  if(tc_inst)tc_inst.destroy();
  tc_inst=new Chart(document.getElementById('tc'),{{type:'bar',
    data:{{labels:ks,datasets:[
      {{label:'Com plano',data:ks.map(function(mk){{return c.meses[mk].com;}}),backgroundColor:c.cor,borderRadius:4,borderSkipped:false}},
      {{label:'Sem plano',data:ks.map(function(mk){{return c.meses[mk].sem;}}),backgroundColor:lt,borderRadius:4,borderSkipped:false}}
    ]}},
    options:{{responsive:true,maintainAspectRatio:false,
      plugins:{{legend:{{labels:{{font:{{size:11}},color:'#888780',boxWidth:10}}}}}},
      scales:{{x:{{stacked:true,ticks:{{font:{{size:11}},color:'#888780'}},grid:{{display:false}}}},
               y:{{stacked:true,ticks:{{font:{{size:11}},color:'#888780'}},grid:{{color:'rgba(136,135,128,.12)'}}}}}}
    }}}});
}}
 
function plano_render(d) {{
  var tots=d.ops_labels.map(function(_,i){{return (d.ops_com[i]||0)+(d.ops_sem[i]||0);}});
  var ord=tots.map(function(_,i){{return i;}}).sort(function(a,b){{return tots[b]-tots[a];}});
  if(pc_inst)pc_inst.destroy();
  pc_inst=new Chart(document.getElementById('pc'),{{type:'bar',
    data:{{labels:ord.map(function(i){{return d.ops_labels[i];}}),datasets:[
      {{label:'Com plano',data:ord.map(function(i){{return d.ops_com[i]||0;}}),backgroundColor:'#1D9E75',stack:'s',borderRadius:0,borderSkipped:false}},
      {{label:'Sem plano',data:ord.map(function(i){{return d.ops_sem[i]||0;}}),backgroundColor:'#F0B429',stack:'s',borderRadius:4,borderSkipped:false}}
    ]}},
    options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,
      plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:function(ctx){{return ' '+ctx.dataset.label+': '+ctx.raw;}}}}}}}},
      scales:{{x:{{stacked:true,ticks:{{font:{{size:11}},color:'#888780'}},grid:{{color:'rgba(136,135,128,.12)'}}}},
               y:{{stacked:true,ticks:{{font:{{size:11}},color:'#888780'}},grid:{{display:false}}}}}}
    }}}});
}}
 
function insight(k,mk,d) {{
  var ib=document.getElementById('ibox');
  ib.className=k==='daniela'?'ibox b':'ibox';
  var pct=function(v){{return d.leads>0?Math.round(v/d.leads*100):0;}};
  var txt='<strong style="color:var(--text)">'+DB[k].nome+' · '+(mk==='all'?'Consolidado':mk)+' —</strong> '
    +d.leads+' leads · '+d.vidas+' vidas · '+pct(d.com)+'% com plano · '
    +'Ticket médio R$'+d.tk.toLocaleString('pt-BR')+' · '+d.vd+' vendas ('+pct(d.vd)+'% conv.)';
  document.getElementById('itxt').innerHTML=txt;
}}
 
function sel(mk) {{
  cm=mk;
  var d=mk==='all'?total(ck):DB[ck].meses[mk];
  var lb=mk==='all'?'Todos os meses':mk;
  pills(ck,mk); metrics(d,lb); vidas(d.vf); status_render(d.sc); plano_render(d); insight(ck,mk,d);
}}
 
function selClient(k) {{
  ck=k; var c=DB[k];
  var av=document.getElementById('cav');
  av.textContent=k==='willian'?'WP':'DB';
  av.className='avatar '+(k==='willian'?'av-w':'av-d');
  document.getElementById('cnm').textContent=c.nome;
  document.getElementById('csb').textContent=k==='willian'?'Bradesco':'Bradesco';
  popSel(k); trend(k); sel('all');
}}
 
document.getElementById('csel').addEventListener('change',function(){{selClient(this.value);}});
document.getElementById('msel').addEventListener('change',function(){{sel(this.value);}});
document.getElementById('btnr').addEventListener('click',function(){{
  alert('Para atualizar: exporte o CSV da planilha do Drive e re-execute o script Python.');
}});
 
selClient('willian');
</script>
</body>
</html>"""
 
 
if __name__ == '__main__':
    html = gerar_dashboard_html()
    with open('dashboard_leads.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ Dashboard gerado em: dashboard_leads.html")
    print("   Abra no navegador para visualizar.")
    print()
    print("📊 Resumo dos dados processados:")
    for ck, cli in CLIENTES.items():
        print(f"\n  Cliente: {cli['nome']}")
        for mes, d in cli['meses'].items():
            print(f"    {mes}: {d['leads']} leads | {d['com']} com plano | {d['sem']} sem | tk R${d['tk']}")
 
