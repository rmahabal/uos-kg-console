"""Per-CU Overview computations (KPIs, composition, readiness, top-bar)."""
import re

COMP_ORDER = ['Product','Feature','Channel','Segment','Customer','Account',
              'RuleThreshold','Authority','Pricing','Policy','Disclosure',
              'DocumentRequirement','Consent','OfferPromotion','Institution','Source']
COMP_LABEL = {'RuleThreshold':'Rule / Threshold','DocumentRequirement':'Document req.',
              'OfferPromotion':'Offer / Promo','Source':'Source (doc/system)'}
# agent groups -> fixed size + the graph domains each group depends on
GROUPS = [
 ('Drive Growth', 10, ['Product','Pricing','OfferPromotion','Segment','Feature']),
 ('Service & Support', 10, ['Channel','DocumentRequirement','Consent','Disclosure']),
 ('Attain Operating Efficiency', 13, ['RuleThreshold','Authority','Source','Pricing']),
 ('Manage Risk & Compliance', 18, ['Policy','Disclosure','Authority','RuleThreshold']),
]
# strict readiness rubric: per-group achievability baselines (front-office deployable vs
# back-office / sign-off-bound). Anchored so a deposits-led community CU reproduces 6/23/22.
READY_BASE = {'Drive Growth':0.25,'Service & Support':0.33,'Attain Operating Efficiency':0.10,'Manage Risk & Compliance':0.03}
BLOCK_BASE = {'Drive Growth':0.25,'Service & Support':0.10,'Attain Operating Efficiency':0.65,'Manage Risk & Compliance':0.42}

def _tilt(arch):
    """archetype tilt: (ready_mult, blocked_mult) per group; None = neutral (deposits-led community)."""
    a=(arch or '').lower()
    if 'lending' in a or 'commercial' in a:
        return {'Drive Growth':(1.0,1.0),'Service & Support':(1.1,0.9),'Attain Operating Efficiency':(0.8,1.15),'Manage Risk & Compliance':(0.7,1.15)}
    if 'full-service' in a:
        return {'Drive Growth':(1.2,0.9),'Service & Support':(1.2,0.9),'Attain Operating Efficiency':(1.1,0.95),'Manage Risk & Compliance':(1.0,1.0)}
    if 'single' in a:
        return {'Drive Growth':(0.8,1.15),'Service & Support':(1.0,1.0),'Attain Operating Efficiency':(0.9,1.05),'Manage Risk & Compliance':(1.0,1.0)}
    return None

def _has_needsfi(n):
    return any(isinstance(v,str) and 'NEEDS_FI' in v for v in n.values())

def compute(d):
    nodes=d['nodes']; edges=d['edges']
    counts={t:len(nodes.get(t,[])) for t in COMP_ORDER}
    total=sum(len(v) for v in nodes.values())
    rel=len(edges)
    oblig=sum(1 for e in edges if e['rel']=='seeds')
    regpacks=len(d.get('reg_linkage',{}).get('packs_seeded',[]))
    conf=sum(1 for v in nodes.values() for n in v if n.get('state') not in (None,'default_unconfirmed'))
    attested=round(100*conf/total) if total else 0
    gaps=sum(1 for v in nodes.values() for n in v if _has_needsfi(n))
    # strict readiness: per-group baseline (deployability) modulated by this CU's
    # confidence profile (hi-share), gap density, domain coverage, and archetype tilt.
    tilt=_tilt(d.get('archetype','')) or {n:(1.0,1.0) for n,_,_ in GROUPS}
    groups=[]; R=P=B=0
    for name,size,doms in GROUPS:
        dn=[n for t in doms for n in nodes.get(t,[])]; pres=len(dn) or 1
        hi=sum(1 for n in dn if isinstance(n.get('confidence_score'),(int,float)) and n['confidence_score']>=0.80)/pres
        gp=sum(1 for n in dn if _has_needsfi(n))/pres
        cov=sum(1 for t in doms if len(nodes.get(t,[]))>=3)/len(doms)
        tr,tb=tilt[name]
        ready=round(size*READY_BASE[name]*(1-0.5*gp)*(0.85+0.3*hi)*tr)
        blocked=round(size*(BLOCK_BASE[name]*(1+0.5*gp)+(1-cov)*0.3)*tb)
        ready=max(0,min(size,ready)); blocked=max(0,min(size-ready,blocked))
        partial=size-ready-blocked
        groups.append((name,ready,partial,blocked)); R+=ready; P+=partial; B+=blocked
    return dict(counts=counts,total=total,rel=rel,oblig=oblig,regpacks=regpacks,
                attested=attested,gaps=gaps,groups=groups,legend=(R,P,B))

def topbar(d):
    fi=d.get('fi','')
    name=fi.split('(')[0].strip()
    paren=re.search(r'\((.*?)\)',fi)
    raw=paren.group(1) if paren else ''
    parts=[p.strip() for p in re.split(r'[;,]',raw) if p.strip() and 'NEEDS_FI' not in p]
    meta=' · '.join(parts)
    inst=(d['nodes'].get('Institution') or [{}])[0]
    asset=inst.get('asset_size')
    if asset and 'NEEDS_FI' not in str(asset) and str(asset) not in meta:
        meta=(meta+' · '+str(asset)).strip(' ·')
    initials=''.join(w[0] for w in name.split()[:2]).upper() or 'FI'
    return name, meta, initials

# ---- Provenance ----
from collections import Counter as _Ctr
_MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
SRC_ICONS=[('var(--sky)','◴'),('var(--teal)','▦'),('var(--lime)','▦'),('var(--amber)','⚑'),('var(--green)','◆'),('var(--purple)','◇')]
def _pretty(s): return ' '.join(w.capitalize() for w in str(s).replace('_',' ').split())
def _short(s,n): s=str(s); return s if len(s)<=n else s[:n-1]+'…'
def _date(s):
    s=str(s or '')
    m=re.match(r'(\d{4})-(\d{2})-(\d{2})',s)
    return (_MON[int(m.group(2))-1]+' '+str(int(m.group(3)))) if m else (s or '—')
def provenance(d):
    nodes=d['nodes']
    cnt=_Ctr()
    for t,arr in nodes.items():
        for n in arr:
            sv=(n.get('source_provenance') or {}).get('source')
            if sv: cnt[sv]+=1
    def _rate(n):
        for f in ('apy_summary','value','rate','rate_tiers','apy','rate_note','notes'):
            v=n.get(f)
            if isinstance(v,str) and v.strip() and 'NEEDS_FI' not in v: return v
        return n.get('name','') or ''
    tnode=None
    for typ in ('Pricing','Product','Disclosure'):
        for n in nodes.get(typ,[]):
            if (n.get('source_provenance') or {}).get('source') and _rate(n).strip():
                tnode=n; break
        if tnode: break
    if tnode is None:
        for arr in nodes.values():
            if arr: tnode=arr[0]; break
    srcs=[]
    for n in nodes.get('Source',[]):
        key=n['id'].split(':',1)[-1]; c=cnt.get(key,0)
        srcs.append((c, n.get('description') or _pretty(key), n.get('type') or 'source', n.get('confidence_score'), n.get('last_sync')))
    srcs.sort(key=lambda x:-x[0])
    rows=[]
    for i,(c,title,cls,conf,date) in enumerate(srcs[:5]):
        col,icon=SRC_ICONS[i%len(SRC_ICONS)]
        tag='tag-ok' if (conf or 0)>=0.75 else 'tag-warn'
        cf=('conf %.2f'%conf) if conf is not None else 'conf —'
        rows.append((col,icon,_short(title,40),'%s · %d nodes'%(cls,c),cf,tag,_date(date)))
    trace=None
    if tnode:
        prov=tnode.get('source_provenance') or {}
        pname=tnode.get('name') or _pretty(tnode['id'].split(':',1)[-1])
        _rw=any(w in pname.lower() for w in ('apy','rate','dividend','par value'))
        _ttl=_short(pname,30) if _rw else _short(pname,26)+' APY'
        trace=dict(title=_ttl, node=tnode['id'],
            src_title=_pretty(prov.get('source','source')),
            src_meta=_short((prov.get('class','') or '')+' · '+str(tnode.get('effective_dates') or tnode.get('effective_from') or ''),40),
            field=_short(_rate(tnode),44),
            field_meta=_short(tnode.get('balance_method','') or '',32),
            gnode='Pricing · v'+str(tnode.get('version','')),
            conf=tnode.get('confidence_score'),
            status=(tnode.get('state','') or '').replace('_','-'))
    meta=dict(owner=(tnode or {}).get('owner','—'),
              effective=str((tnode or {}).get('effective_from','—')),
              version='v'+str(d.get('version','')).replace('-DRAFT','')+' · '+str(d.get('built','')),
              pii=(tnode or {}).get('pii_classification','none'))
    return dict(trace=trace, meta=meta, nsrc=len(nodes.get('Source',[])), sync=_date(d.get('built','')), rows=rows)

# ---- Overview bottom cards ----
def cards(d):
    nodes=d['nodes']
    confs=[n.get('confidence_score') for t in nodes for n in nodes[t] if isinstance(n.get('confidence_score'),(int,float))]
    avg=round(sum(confs)/len(confs),2) if confs else 0
    b1=sum(1 for c in confs if c>=0.85); b2=sum(1 for c in confs if 0.70<=c<0.85)
    b3=sum(1 for c in confs if 0.50<=c<0.70); b4=sum(1 for c in confs if c<0.50)
    packs=(d.get('reg_linkage',{}) or {}).get('packs_seeded',[]) or []
    oblig=sum(1 for e in d.get('edges',[]) if e.get('rel')=='seeds')
    gaps=sum(1 for t in nodes for n in nodes[t] if _has_needsfi(n))
    total=sum(len(v) for v in nodes.values()); rel=len(d.get('edges',[]))
    # top gaps: node types with most NEEDS_FI, as readable rows
    GAP_LABEL={'Authority':'Account-opening authority & approval thresholds','Policy':'Governing policies — full text & domains',
      'RuleThreshold':'Operational rules & thresholds','Disclosure':'Disclosures — type & source document',
      'DocumentRequirement':'Document requirements by applicant type','Pricing':'Pricing — rate tiers & fee schedules',
      'Feature':'Product features — default-issue flags','Consent':'Consent artifacts & channel opt-ins','OfferPromotion':'Promotion eligibility & stacking rules'}
    GAP_HINT={'Authority':'who can open, autonomy level, approver role','Policy':'domain, full policy text','RuleThreshold':'condition, outcome action',
      'Disclosure':'type, source document','DocumentRequirement':'applicant type, required docs','Pricing':'rate tiers, fee schedule',
      'Feature':'default-issue flag, cost','Consent':'consent text, channel','OfferPromotion':'eligibility, stacking rules'}
    nf_by_type=[]
    for t in nodes:
        c=sum(1 for n in nodes[t] if _has_needsfi(n))
        if c>0 and t in GAP_LABEL: nf_by_type.append((c,t))
    nf_by_type.sort(reverse=True)
    topgaps=[]
    for c,t in nf_by_type[:4]:
        topgaps.append((GAP_LABEL[t], GAP_HINT.get(t,''), max(1,min(5,c//8))))
    return dict(avg=avg,b1=b1,b2=b2,b3=b3,b4=b4,packs=packs,more=max(0,25-len(packs)),
                oblig=oblig,gaps=gaps,total=total,rel=rel,archetype=d.get('archetype',''),topgaps=topgaps)
# eof
