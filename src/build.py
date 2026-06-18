"""Generate standalone per-CU console pages: graph + top-bar + Overview + Provenance, baked into the template."""
import json, os, re, html as _h
_c={}; exec(open('convert.py').read(), _c); convert_instance=_c['convert_instance']
_m={}; exec(open('compute.py').read(), _m)
compute=_m['compute']; topbar=_m['topbar']; provenance=_m['provenance']; COMP_ORDER=_m['COMP_ORDER']; cards=_m['cards']
_cb={}; exec(open('cards_bind.py').read(), _cb); bind_cards=_cb['bind_cards']
TEMPLATE='_template_console.html'
CUS={'ccu':'data/ccu.json','farmers':'data/farmers.json','iccu':'data/iccu.json','mission':'data/mission.json'}
COMP_TLABEL={'RuleThreshold':'Rule / Threshold','DocumentRequirement':'Document req.','OfferPromotion':'Offer / Promo','Source':'Source (doc/system)'}
E=_h.escape

def sub1(s, old, new):
    assert old in s, 'anchor missing: '+old[:60]
    return s.replace(old, new, 1)

_GEN_REASON={'ready':'knowledge present · pending sign-off',
             'partial':'partial knowledge · some at runtime',
             'blocked':'required module or pack not loaded'}
_RANK={'ready':2,'partial':1,'blocked':0}
_AITEM=re.compile(r'<div class="a-item"><span class="adot (\w+)"></span><div><div class="an">(.*?)</div><div class="ar">(.*?)</div></div><span class="as \w+">.*?</span></div>', re.S)

def _aitem_html(status,name,reason):
    return ('<div class="a-item"><span class="adot '+status+'"></span><div><div class="an">'+name+
            '</div><div class="ar">'+reason+'</div></div><span class="as '+status+'">'+status.capitalize()+'</span></div>')

def rethread(s, groups):
    """Re-bucket the universal 51-agent list per-CU so each agent's dot matches the rubric counts.
    Preserves CCU deployability order + bespoke reasons; swaps reason only when an agent's bucket changes."""
    gmap={name:(r,p,b) for name,r,p,b in groups}
    blocks=re.findall(r'<div class="agroup"><div class="gh"><span class="gt">([^<]*)</span><span class="gc">([^<]*)</span></div><div class="alist">((?:<div class="a-item">.*?</span></div>)+)</div></div>', s, re.S)
    for gname,gc_old,alist in blocks:
        if gname not in gmap: continue
        r,p,b=gmap[gname]
        agents=[(st,nm,rs) for st,nm,rs in _AITEM.findall(alist)]
        order=sorted(range(len(agents)), key=lambda i:(-_RANK[agents[i][0]], i))  # deployability desc, stable
        new_status={}
        for rank,idx in enumerate(order):
            new_status[idx]= 'ready' if rank<r else ('partial' if rank<r+p else 'blocked')
        items=''
        for i,(st,nm,rs) in enumerate(agents):
            ns=new_status[i]
            reason= rs if ns==st else _GEN_REASON[ns]
            items+=_aitem_html(ns,nm,reason)
        new_block=('<div class="agroup"><div class="gh"><span class="gt">'+gname+'</span><span class="gc">'+
                   '%dR · %dP · %dB · %d agents'%(r,p,b,r+p+b)+'</span></div><div class="alist">'+items+'</div></div>')
        old_block='<div class="agroup"><div class="gh"><span class="gt">'+gname+'</span><span class="gc">'+gc_old+'</span></div><div class="alist">'+alist+'</div></div>'
        s=s.replace(old_block,new_block,1)
    return s

def focus_sentence(arch, acro):
    a=(arch or '').lower()
    if 'lending' in a or 'commercial' in a:
        return acro+' is a lending- and commercial-focused institution, so credit and servicing agents reach further; pure back-office efficiency and parts of risk stay blocked until those systems load.'
    if 'full-service' in a:
        return acro+' is a full-service community institution, so front-office agents lead broadly; deep back-office and specialized risk agents stay blocked until those modules load.'
    if 'single' in a:
        return acro+' is a single-segment consumer-deposits CU, so a focused set of deposit &amp; service agents lead; lending, business and efficiency agents stay blocked until those modules load.'
    return acro+' is a deposits-led consumer core, so front-office deposit &amp; service agents lead; lending, business and most efficiency agents stay blocked until those modules load.'

def build(cu, src):
    d=json.load(open(src)); g=convert_instance(d); o=compute(d); name,meta,av=topbar(d); pv=provenance(d)
    lines=open(TEMPLATE,encoding='utf-8').read().split('\n')
    gi=next(i for i,ln in enumerate(lines) if ln.strip().startswith('var G={'))
    lines[gi]='var G='+json.dumps(g,ensure_ascii=False)+';window.__KG=G;'; s='\n'.join(lines)
    s=s.replace('ccu_graph.json?v=','__baked__.json?v=')
    inst_id=next((nid for nid,n in g['nodes'].items() if n['k']=='inst'),'INST:ccu')
    s=s.replace("center='INST:ccu'","center='"+inst_id+"'")
    # --- revive JS-driven views: feed the inline per-CU graph to every fetch handler ---
    s=s.replace("JSON.parse(xhr.responseText)","(window.__KG||{nodes:{},edges:[]})")
    s=s.replace("JSON.parse(__x.responseText)","(window.__KG||{nodes:{},edges:[]})")
    s=s.replace("(xhr.status>=200&&xhr.status<400)||xhr.status===0","true")
    s=s.replace("(__x.status>=200&&__x.status<400)||__x.status===0","true")
    s=s.replace("var TOTAL=445","var TOTAL="+str(o['total']))
    # default node ids that other CUs don't have -> valid per-CU ids
    prod_id=next((nid for nid,n in g['nodes'].items() if n['k']=='prod'),'')
    s=s.replace("curId='PRC:share_savings'","curId='"+pv['trace']['node']+"'")
    s=s.replace("'PRC:share_savings'","'"+pv['trace']['node']+"'")
    if prod_id: s=s.replace("'PR:share_savings'","'"+prod_id+"'")
    # top bar
    s=sub1(s,'<div class="av">CC</div>','<div class="av">'+E(av)+'</div>')
    s=sub1(s,'<div class="nm">California Credit Union</div>','<div class="nm">'+E(name)+'</div>')
    s=sub1(s,'<div class="meta">NCUA #24980 · DFPI #9530137 · ~$1.3B</div>','<div class="meta">'+E(meta)+'</div>')
    # KPIs
    s=sub1(s,'<div class="val">445</div><div class="sub">across 16 object types</div>','<div class="val">%d</div><div class="sub">across 16 object types</div>'%o['total'])
    s=sub1(s,'<div class="val">781</div><div class="sub">614 obligation links</div>','<div class="val">%d</div><div class="sub">%d obligation links</div>'%(o['rel'],o['oblig']))
    s=sub1(s,'id="kpi-attested">0%</div>','id="kpi-attested">%d%%</div>'%o['attested'])
    s=sub1(s,'<div class="val">68</div><div class="sub">NEEDS_FI items</div>','<div class="val">%d</div><div class="sub">NEEDS_FI items</div>'%o['gaps'])
    s=sub1(s,'<div class="val">10</div><div class="sub">of 25 in library</div>','<div class="val">%d</div><div class="sub">of 25 in library</div>'%o['regpacks'])
    # ---- Sign-off Queue KPIs (static CCU literals -> per-CU) ----
    ready=o['total']-o['gaps']
    s=sub1(s,'id="kpi-awaiting">445</div>','id="kpi-awaiting">%d</div>'%o['total'])
    s=sub1(s,'<div class="lab">Your queue</div><div class="val">68</div>','<div class="lab">Your queue</div><div class="val">%d</div>'%o['gaps'])
    s=sub1(s,'id="bulk-attest">Bulk attest DEP pack (124)','id="bulk-attest">Bulk attest ready set (%d)'%ready)
    s=s.replace("bulk.textContent='✓ DEP pack attested'","bulk.textContent='✓ ready set attested'")
    s=s.replace("ratified+=124; update(); toast('DEP pack attested · 124 nodes ratified · deposit agents promoted')","ratified+=%d; update(); toast('%d nodes ratified · agents promoted')"%(ready,ready))
    # composition
    maxc=max(o['counts'].values()) or 1
    for t in COMP_ORDER:
        lbl=COMP_TLABEL.get(t,t); c=o['counts'][t]; w=round(100*c/maxc); disp=str(c)+('*' if t in ('Customer','Account') else '')
        pat=r'(<span class="on">'+re.escape(lbl)+r'</span><span class="bar"><i style="width:)[^"]*("></i></span><span class="oc">)[^<]*(</span>)'
        s=re.sub(pat, lambda m,w=w,disp=disp: m.group(1)+('%d%%'%w)+m.group(2)+disp+m.group(3), s, count=1)
    # readiness
    for (gname,r,p,b),(_,size,_) in zip(o['groups'], _m['GROUPS']):
        wr,wp,wb=round(100*r/size),round(100*p/size),round(100*b/size)
        pat=(r'(<span class="bg-name">'+re.escape(gname)+r'</span><span class="bg-count">)[^<]*(</span></div><div class="sbar"><i class="r" style="width:)[^"]*("></i><i class="p" style="width:)[^"]*("></i><i class="b" style="width:)[^"]*(%?"></i>)')
        rep=lambda m,r=r,p=p,b=b,wr=wr,wp=wp,wb=wb: (m.group(1)+'%d ready · %d partial · %d blocked'%(r,p,b)+m.group(2)+'%d%%'%wr+m.group(3)+'%d%%'%wp+m.group(4)+('%d%%'%wb if not m.group(5) else '%d'%wb)+m.group(5))
        s=re.sub(pat, rep, s, count=1)
    R,P,B=o['legend']
    s=re.sub(r'Ready \(\d+\)','Ready (%d)'%R,s,count=1); s=re.sub(r'Partial \(\d+\)','Partial (%d)'%P,s,count=1); s=re.sub(r'Blocked \(\d+\)','Blocked (%d)'%B,s,count=1)
    # ---- Gaps page: KPI cards (were static CCU) + re-thread 51-agent list + narrative ----
    _acro_n=''.join(w[0] for w in name.split() if w[:1].isalpha()).upper()[:5] or 'FI'
    s=sub1(s,'<div class="lab">Agents ready</div><div class="val">6</div>','<div class="lab">Agents ready</div><div class="val">%d</div>'%R)
    s=sub1(s,'<div class="lab">Partial</div><div class="val warn">23</div>','<div class="lab">Partial</div><div class="val warn">%d</div>'%P)
    s=sub1(s,'<div class="lab">Blocked</div><div class="val">22</div>','<div class="lab">Blocked</div><div class="val">%d</div>'%B)
    s=rethread(s, o['groups'])
    s=sub1(s,'CCU is deposits-led consumer core, so front-office deposit &amp; service agents lead; lending, business and most efficiency agents are blocked until those modules load.', focus_sentence(d.get('archetype',''), _acro_n))
    # ---- Overview bottom cards + title + archetype ----
    s=bind_cards(s, d, o, name, av, cards)
    # ---- Provenance ----
    tr=pv['trace']; pm=pv['meta']
    s=sub1(s,'<h3>Trace · Share Savings APY</h3><span class="hint">node PRC:share_savings</span>','<h3>Trace · '+E(tr['title'])+'</h3><span class="hint">node '+E(tr['node'])+'</span>')
    s=sub1(s,'<div class="ct">Source</div><div class="cv">Consumer Ratesheet</div><div class="cm">PDF · 03.02.26 · ccu.com</div>','<div class="ct">Source</div><div class="cv">'+E(tr['src_title'])+'</div><div class="cm">'+E(tr['src_meta'])+'</div>')
    s=sub1(s,'<div class="ct">Extracted field</div><div class="cv">"0.05% APY $100+"</div><div class="cm">daily balance, monthly</div>','<div class="ct">Extracted field</div><div class="cv">"'+E(tr['field'])+'"</div><div class="cm">'+E(tr['field_meta'])+'</div>')
    s=sub1(s,'<div class="ct">Graph node</div><div class="cv">Pricing · v0.9</div><div class="cm">confidence 0.85</div>','<div class="ct">Graph node</div><div class="cv">'+E(tr['gnode'])+'</div><div class="cm">confidence '+(('%.2f'%tr['conf']) if tr['conf'] is not None else '—')+'</div>')
    s=sub1(s,'<div class="cv" style="color:var(--amber)">default-unconfirmed</div><div class="cm">awaiting FI sign-off</div>','<div class="cv" style="color:var(--amber)">'+E(tr['status'])+'</div><div class="cm">awaiting FI sign-off</div>')
    s=sub1(s,'<div class="l">Owner</div><div class="v">Product / Finance</div>','<div class="l">Owner</div><div class="v">'+E(pm['owner'])+'</div>')
    s=sub1(s,'<div class="l">Effective from</div><div class="v">2026-03-02</div>','<div class="l">Effective from</div><div class="v">'+E(pm['effective'])+'</div>')
    s=sub1(s,'<div class="l">As-of (graph version)</div><div class="v">v1.2 · 2026-06-12</div>','<div class="l">As-of (graph version)</div><div class="v">'+E(pm['version'])+'</div>')
    s=sub1(s,'<div class="l">PII classification</div><div class="v">none</div>','<div class="l">PII classification</div><div class="v">'+E(pm['pii'])+'</div>')
    s=sub1(s,'<span class="hint">14 sources · last sync 2026-06-12</span>','<span class="hint">'+str(pv['nsrc'])+' sources · last sync '+E(pv['sync'])+'</span>')
    rows=''
    for col,icon,title,rmeta,cf,tag,date in pv['rows']:
        rows+=('<div class="lrow"><span class="fi-ic" style="background:'+col+'">'+icon+'</span><div><div class="lt">'+E(title)+'</div><div class="lm">'+E(rmeta)+'</div></div><span class="'+tag+'">'+E(cf)+'</span><span class="lm">'+E(date)+'</span></div>')
    def _rl(m): return m.group(1)+rows+m.group(2)
    s=re.sub(r'(<h3>Source register</h3>.*?<div class="row-list">).*?(</div>\s*</section>)', _rl, s, count=1, flags=re.S)
    # ---- sweep any remaining hardcoded CCU/California text (skip the inline-data line) ----
    acro=''.join(w[0] for w in name.split() if w[:1].isalpha()).upper()[:5] or 'FI'
    _fl=s.split('\n')
    for _i in range(len(_fl)):
        if _fl[_i].startswith('var G='): continue
        _fl[_i]=_fl[_i].replace('California Credit Union',name).replace('California CU',name)
        _fl[_i]=re.sub(r'\bCCU\b',acro,_fl[_i])
    s='\n'.join(_fl)
    os.makedirs('pages',exist_ok=True); dst='pages/console-'+cu+'.html'; open(dst,'w',encoding='utf-8').write(s)
    return dst,o,name,tr

if __name__=='__main__':
    for cu,src in CUS.items():
        dst,o,name,tr=build(cu,src)
        print('%-8s %-38s nodes=%d edges=%d | trace=%s'%(cu,name,o['total'],o['rel'],tr['title']))
# eof
