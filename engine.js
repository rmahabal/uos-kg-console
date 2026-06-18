/* Browser port of convert.py + compute.py + build.py — turns an instance JSON into a console page. */
(function(global){
const TYPE2K={Institution:'inst',Product:'prod',Feature:'feat',Segment:'seg',Channel:'chan',RuleThreshold:'rule',Pricing:'price',Authority:'auth',Policy:'pol',Disclosure:'disc',DocumentRequirement:'doc',OfferPromotion:'offer',Consent:'cons',Source:'src',Customer:'cust',Account:'acct'};
const KL={inst:'Institution',prod:'Product',feat:'Feature',seg:'Segment',chan:'Channel',rule:'Rule',price:'Pricing',auth:'Authority',pol:'Policy',disc:'Disclosure',doc:'Doc Req',offer:'Offer',cons:'Consent',src:'Source',cust:'Customer',acct:'Account'};
const FIELD={inst:'legal_name',prod:'features',feat:'type',seg:'definition_criteria',chan:'description',rule:'condition',price:'apy_summary',auth:'action',pol:'domain',disc:'type',doc:'applicant_type',offer:'incentive',cons:'name',src:'description'};
const COMP_ORDER=['Product','Feature','Channel','Segment','Customer','Account','RuleThreshold','Authority','Pricing','Policy','Disclosure','DocumentRequirement','Consent','OfferPromotion','Institution','Source'];
const COMP_TLABEL={RuleThreshold:'Rule / Threshold',DocumentRequirement:'Document req.',OfferPromotion:'Offer / Promo',Source:'Source (doc/system)'};
const GROUPS=[['Drive Growth',10,['Product','Pricing','OfferPromotion','Segment','Feature']],['Service & Support',10,['Channel','DocumentRequirement','Consent','Disclosure']],['Attain Operating Efficiency',13,['RuleThreshold','Authority','Source','Pricing']],['Manage Risk & Compliance',18,['Policy','Disclosure','Authority','RuleThreshold']]];
const READY_BASE={'Drive Growth':0.25,'Service & Support':0.33,'Attain Operating Efficiency':0.10,'Manage Risk & Compliance':0.03};
const BLOCK_BASE={'Drive Growth':0.25,'Service & Support':0.10,'Attain Operating Efficiency':0.65,'Manage Risk & Compliance':0.42};
function _tilt(arch){const a=(arch||'').toLowerCase();
  if(a.indexOf('lending')>=0||a.indexOf('commercial')>=0)return {'Drive Growth':[1.0,1.0],'Service & Support':[1.1,0.9],'Attain Operating Efficiency':[0.8,1.15],'Manage Risk & Compliance':[0.7,1.15]};
  if(a.indexOf('full-service')>=0)return {'Drive Growth':[1.2,0.9],'Service & Support':[1.2,0.9],'Attain Operating Efficiency':[1.1,0.95],'Manage Risk & Compliance':[1.0,1.0]};
  if(a.indexOf('single')>=0)return {'Drive Growth':[0.8,1.15],'Service & Support':[1.0,1.0],'Attain Operating Efficiency':[0.9,1.05],'Manage Risk & Compliance':[1.0,1.0]};
  return null;}
const _GEN_REASON={ready:'knowledge present · pending sign-off',partial:'partial knowledge · some at runtime',blocked:'required module or pack not loaded'};
const _RANK={ready:2,partial:1,blocked:0};
const MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const cap=s=>s.split(/\s+/).filter(Boolean).map(w=>w.charAt(0).toUpperCase()+w.slice(1)).join(' ');
const titleFromId=id=>cap(String(id).split(':').slice(1).join(':').replace(/_/g,' '));
const E=s=>String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const esc=s=>String(s).replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
const hasNF=n=>Object.values(n).some(v=>typeof v==='string'&&v.indexOf('NEEDS_FI')>=0);
const dstr=s=>{const m=/(\d{4})-(\d{2})-(\d{2})/.exec(String(s||''));return m?MON[+m[2]-1]+' '+(+m[3]):(s||'—');};
const short=(s,n)=>{s=String(s==null?'':s);return s.length<=n?s:s.slice(0,n-1)+'…';};

function convert(d){
  const nodes={};
  for(const t in d.nodes){const k=TYPE2K[t]||t.toLowerCase();
    for(const n of d.nodes[t]){const prov=n.source_provenance||{},conf=n.confidence_score,srcn=prov.source||'';
      let fv=n[FIELD[k]]; if(Array.isArray(fv))fv=fv.join(', '); if(fv==null)fv=n.name||'';
      nodes[n.id]={id:n.id,k:k,kl:KL[k]||t,name:n.name||titleFromId(n.id),nf:false,conf:conf,
        src:srcn?(srcn+' · conf '+conf):'',ver:n.version,eff:n.effective_from,effto:n.effective_to||'—',
        owner:n.owner,pii:n.pii_classification,st:n.state,url:prov.url||'',cls:prov.class||'',srcn:srcn,field:fv};}}
  const edges=(d.edges||[]).map(e=>[e.from,e.to,e.rel]);
  return {nodes:nodes,edges:edges};
}
function compute(d){
  const nodes=d.nodes,edges=d.edges||[];
  const counts={}; COMP_ORDER.forEach(t=>counts[t]=(nodes[t]||[]).length);
  let total=0; for(const t in nodes)total+=nodes[t].length;
  const rel=edges.length, oblig=edges.filter(e=>e.rel==='seeds').length;
  const regpacks=((d.reg_linkage||{}).packs_seeded||[]).length;
  let conf=0; for(const t in nodes)for(const n of nodes[t])if(n.state&&n.state!=='default_unconfirmed')conf++;
  const attested=total?Math.round(100*conf/total):0;
  let gaps=0; for(const t in nodes)for(const n of nodes[t])if(hasNF(n))gaps++;
  const tilt=_tilt(d.archetype||'')||(function(){const o={};GROUPS.forEach(g=>o[g[0]]=[1,1]);return o;})();
  const groups=[]; let R=0,P=0,B=0;
  for(const [name,size,doms] of GROUPS){
    const dn=[]; doms.forEach(t=>(nodes[t]||[]).forEach(n=>dn.push(n))); const pres=dn.length||1;
    const hi=dn.filter(n=>typeof n.confidence_score==='number'&&n.confidence_score>=0.80).length/pres;
    const gp=dn.filter(hasNF).length/pres;
    const cov=doms.filter(t=>(nodes[t]||[]).length>=3).length/doms.length;
    const tr=tilt[name][0], tb=tilt[name][1];
    let ready=Math.round(size*READY_BASE[name]*(1-0.5*gp)*(0.85+0.3*hi)*tr);
    let blocked=Math.round(size*(BLOCK_BASE[name]*(1+0.5*gp)+(1-cov)*0.3)*tb);
    ready=Math.max(0,Math.min(size,ready)); blocked=Math.max(0,Math.min(size-ready,blocked));
    const partial=size-ready-blocked; groups.push([name,ready,partial,blocked]); R+=ready;P+=partial;B+=blocked;}
  return {counts,total,rel,oblig,regpacks,attested,gaps,groups,legend:[R,P,B]};
}
function topbar(d){
  const fi=d.fi||''; const name=fi.split('(')[0].trim();
  const pm=/\((.*?)\)/.exec(fi); let meta='';
  if(pm)meta=pm[1].split(/[;,]/).map(x=>x.trim()).filter(x=>x&&x.indexOf('NEEDS_FI')<0).join(' · ');
  const inst=(d.nodes.Institution||[{}])[0]; const asset=inst.asset_size;
  if(asset&&String(asset).indexOf('NEEDS_FI')<0&&meta.indexOf(String(asset))<0)meta=(meta+' · '+asset).replace(/^ · /,'');
  const initials=(name.split(/\s+/).slice(0,2).map(w=>w[0]).join('')||'FI').toUpperCase();
  return {name,meta,av:initials};
}
function provenance(d){
  const nodes=d.nodes; const cnt={};
  for(const t in nodes)for(const n of nodes[t]){const s=(n.source_provenance||{}).source;if(s)cnt[s]=(cnt[s]||0)+1;}
  const rate=n=>{for(const f of['apy_summary','value','rate','rate_tiers','apy','rate_note','notes']){const v=n[f];if(typeof v==='string'&&v.trim()&&v.indexOf('NEEDS_FI')<0)return v;}return n.name||'';};
  let tn=null;
  for(const typ of['Pricing','Product','Disclosure']){for(const n of (nodes[typ]||[])){if((n.source_provenance||{}).source&&rate(n).trim()){tn=n;break;}}if(tn)break;}
  if(!tn){for(const t in nodes){if(nodes[t].length){tn=nodes[t][0];break;}}}
  const srcs=(nodes.Source||[]).map(n=>{const key=n.id.split(':').slice(1).join(':');return [cnt[key]||0,n.description||titleFromId(n.id),n.type||'source',n.confidence_score,n.last_sync];}).sort((a,b)=>b[0]-a[0]);
  const ICON=[['var(--sky)','◴'],['var(--teal)','▦'],['var(--lime)','▦'],['var(--amber)','⚑'],['var(--green)','◆']];
  const rows=srcs.slice(0,5).map((r,i)=>{const conf=r[3];const cf=conf!=null?('conf '+conf.toFixed(2)):'conf —';return {col:ICON[i%5][0],icon:ICON[i%5][1],title:short(r[1],40),meta:r[2]+' · '+r[0]+' nodes',cf:cf,tag:(conf||0)>=0.75?'tag-ok':'tag-warn',date:dstr(r[4])};});
  let trace=null;
  if(tn){const prov=tn.source_provenance||{};const pn=tn.name||titleFromId(tn.id);
    const rw=['apy','rate','dividend','par value'].some(w=>pn.toLowerCase().indexOf(w)>=0);
    trace={title:rw?short(pn,30):short(pn,26)+' APY',node:tn.id,src_title:cap(prov.source||'source'),
      src_meta:short((prov.class||'')+' · '+(tn.effective_dates||tn.effective_from||''),40),
      field:short(rate(tn),44),field_meta:short(tn.balance_method||'',32),gnode:'Pricing · v'+(tn.version||''),
      conf:tn.confidence_score,status:String(tn.state||'').replace(/_/g,'-')};}
  const meta={owner:(tn||{}).owner||'—',effective:String((tn||{}).effective_from||'—'),
    version:'v'+String(d.version||'').replace('-DRAFT','')+' · '+(d.built||''),pii:(tn||{}).pii_classification||'none'};
  return {trace,meta,nsrc:(nodes.Source||[]).length,sync:dstr(d.built||''),rows};
}
function rep1(s,a,b){const i=s.indexOf(a);return i<0?s:s.slice(0,i)+b+s.slice(i+a.length);}
function cards(d){
  const nodes=d.nodes; const confs=[];
  for(const t in nodes)for(const n of nodes[t])if(typeof n.confidence_score==='number')confs.push(n.confidence_score);
  const avg=confs.length?Math.round(100*confs.reduce((a,b)=>a+b,0)/confs.length)/100:0;
  const b1=confs.filter(c=>c>=0.85).length,b2=confs.filter(c=>c>=0.70&&c<0.85).length,b3=confs.filter(c=>c>=0.50&&c<0.70).length,b4=confs.filter(c=>c<0.50).length;
  const packs=((d.reg_linkage||{}).packs_seeded)||[];
  const oblig=(d.edges||[]).filter(e=>e.rel==='seeds').length;
  let gaps=0,total=0; for(const t in nodes){total+=nodes[t].length; for(const n of nodes[t])if(hasNF(n))gaps++;}
  const GL={Authority:'Account-opening authority & approval thresholds',Policy:'Governing policies — full text & domains',RuleThreshold:'Operational rules & thresholds',Disclosure:'Disclosures — type & source document',DocumentRequirement:'Document requirements by applicant type',Pricing:'Pricing — rate tiers & fee schedules',Feature:'Product features — default-issue flags',Consent:'Consent artifacts & channel opt-ins',OfferPromotion:'Promotion eligibility & stacking rules'};
  const GH={Authority:'who can open, autonomy level, approver role',Policy:'domain, full policy text',RuleThreshold:'condition, outcome action',Disclosure:'type, source document',DocumentRequirement:'applicant type, required docs',Pricing:'rate tiers, fee schedule',Feature:'default-issue flag, cost',Consent:'consent text, channel',OfferPromotion:'eligibility, stacking rules'};
  const nf=[]; for(const t in nodes){if(!(t in GL))continue; const c=nodes[t].filter(hasNF).length; if(c>0)nf.push([c,t]);}
  nf.sort((a,b)=>b[0]-a[0]);
  const topgaps=nf.slice(0,4).map(x=>[GL[x[1]],GH[x[1]]||'',Math.max(1,Math.min(5,Math.floor(x[0]/8)))]);
  return {avg,b1,b2,b3,b4,packs,more:Math.max(0,25-packs.length),oblig,gaps,total,rel:(d.edges||[]).length,archetype:d.archetype||'',topgaps};
}
function bindCards(s,d,o,name,av){
  const cd=cards(d); const arch=(cd.archetype||'').toLowerCase();
  const charter=(/federal| fcu/.test(arch))?'Federal':(/state/.test(arch)?'State-chartered':'Chartered');
  const focus=/lending/.test(arch)?'lending-led':(/commercial/.test(arch)?'commercial':'deposits-led');
  const archlabel=charter+' · '+focus;
  const acro=(name.split(/\s+/).filter(w=>/[A-Za-z]/.test(w[0]||'')).map(w=>w[0]).join('').toUpperCase().slice(0,5))||av;
  const R=(a,b)=>{s=s.split(a).join(b);};
  R('<title>Knowledge Graph Console · California CU · UOS</title>','<title>Knowledge Graph Console · '+E(name)+' · UOS</title>');
  R('<span class="pill">State-chartered · deposits-led</span>','<span class="pill">'+E(archlabel)+'</span>');
  R('<div class="big"><b>0 / 445</b><span>nodes attested by CCU</span></div>','<div class="big"><b>0 / '+cd.total+'</b><span>nodes attested by '+E(acro)+'</span></div>');
  R('Source confidence (avg 0.66)','Source confidence (avg '+cd.avg.toFixed(2)+')');
  R('0.85+ · 68','0.85+ · '+cd.b1);R('0.70–0.84 · 49','0.70–0.84 · '+cd.b2);R('0.50–0.69 · 327','0.50–0.69 · '+cd.b3);R('&lt;0.5 · 1','&lt;0.5 · '+cd.b4);
  R('<h3>Regulatory coverage</h3><span class="more">10 / 25 packs</span>','<h3>Regulatory coverage</h3><span class="more">'+o.regpacks+' / 25 packs</span>');
  R('<div class="chips" style="margin-bottom:12px"><span class="chip on">DEP</span><span class="chip on">CIP-BSA</span><span class="chip on">PRIV-SEC</span><span class="chip on">FRAUD</span><span class="chip on">SERV-DEP</span><span class="chip on">DISPUTES</span><span class="chip on">CONS-COMPLIANCE</span><span class="chip on">PAY</span><span class="chip on">CARDS</span><span class="chip on">COMMS</span></div>','<div class="chips" style="margin-bottom:12px">'+cd.packs.map(p=>'<span class="chip on">'+E(p)+'</span>').join('')+'</div>');
  R('15 more in the 25-pack library · not yet loaded',cd.more+' more in the 25-pack library · not yet loaded');
  R('CCU is a deposits-led consumer core.',E(acro)+' is a '+focus+' institution.');
  R('Graph composed — 445 nodes, 781 edges','Graph composed — '+cd.total+' nodes, '+cd.rel+' edges');
  R('10 reg packs seeded · 614 obligations wired 1:1',o.regpacks+' reg packs seeded · '+cd.oblig+' obligations wired 1:1');
  R('DEP, CIP-BSA, PRIV-SEC … COMMS',E(cd.packs.slice(0,3).join(', ')+(cd.packs.length>3?(' … '+cd.packs[cd.packs.length-1]):'')));
  R('68 items flagged NEEDS_FI',cd.gaps+' items flagged NEEDS_FI');
  const gh=cd.topgaps.map(x=>'<div class="gap"><div class="gt">'+E(x[0])+' <span class="gm">— '+E(x[1])+'</span></div><span class="gb">blocks '+x[2]+' agents</span></div>').join('')||'<div class="gap"><div class="gt">No open gaps — all knowledge present</div></div>';
  s=s.replace(/(Top gaps to close · NEEDS_FI<\/h3>[\s\S]*?<div>)[\s\S]*?(<\/div>\s*<\/section>)/,(m,a,b)=>a+gh+b);
  return s;
}
function rethread(s,groups){
  const gmap={}; groups.forEach(g=>gmap[g[0]]=[g[1],g[2],g[3]]);
  const re=/<div class="agroup"><div class="gh"><span class="gt">([^<]*)<\/span><span class="gc">([^<]*)<\/span><\/div><div class="alist">((?:<div class="a-item">[\s\S]*?<\/span><\/div>)+)<\/div><\/div>/g;
  const aitem=/<div class="a-item"><span class="adot (\w+)"><\/span><div><div class="an">([\s\S]*?)<\/div><div class="ar">([\s\S]*?)<\/div><\/div><span class="as \w+">[\s\S]*?<\/span><\/div>/g;
  return s.replace(re,function(m,gname,gcOld,alist){
    if(!gmap[gname])return m;
    const r=gmap[gname][0],p=gmap[gname][1],b=gmap[gname][2]; const agents=[]; let am;
    aitem.lastIndex=0; while((am=aitem.exec(alist))!==null) agents.push([am[1],am[2],am[3]]);
    const order=agents.map((a,i)=>i).sort((x,y)=>(_RANK[agents[y][0]]-_RANK[agents[x][0]])||(x-y));
    const ns={}; order.forEach((idx,rank)=>{ns[idx]= rank<r?'ready':(rank<r+p?'partial':'blocked');});
    let items=''; agents.forEach(function(a,i){const st=ns[i]; const reason=(st===a[0])?a[2]:_GEN_REASON[st];
      items+='<div class="a-item"><span class="adot '+st+'"></span><div><div class="an">'+a[1]+'</div><div class="ar">'+reason+'</div></div><span class="as '+st+'">'+st.charAt(0).toUpperCase()+st.slice(1)+'</span></div>';});
    return '<div class="agroup"><div class="gh"><span class="gt">'+gname+'</span><span class="gc">'+r+'R · '+p+'P · '+b+'B · '+(r+p+b)+' agents</span></div><div class="alist">'+items+'</div></div>';
  });
}
function focusSentence(arch,acro){const a=(arch||'').toLowerCase();
  if(a.indexOf('lending')>=0||a.indexOf('commercial')>=0)return acro+' is a lending- and commercial-focused institution, so credit and servicing agents reach further; pure back-office efficiency and parts of risk stay blocked until those systems load.';
  if(a.indexOf('full-service')>=0)return acro+' is a full-service community institution, so front-office agents lead broadly; deep back-office and specialized risk agents stay blocked until those modules load.';
  if(a.indexOf('single')>=0)return acro+' is a single-segment consumer-deposits CU, so a focused set of deposit &amp; service agents lead; lending, business and efficiency agents stay blocked until those modules load.';
  return acro+' is a deposits-led consumer core, so front-office deposit &amp; service agents lead; lending, business and most efficiency agents stay blocked until those modules load.';
}
function buildPage(template,d){
  const g=convert(d),o=compute(d),tb=topbar(d),pv=provenance(d);
  let lines=template.split('\n'); const gi=lines.findIndex(l=>l.trim().indexOf('var G={')===0);
  lines[gi]='var G='+JSON.stringify(g)+';window.__KG=G;'; let s=lines.join('\n');
  s=s.split('ccu_graph.json?v=').join('__baked__.json?v=');
  const inst=Object.values(g.nodes).find(n=>n.k==='inst'); s=s.split("center='INST:ccu'").join("center='"+(inst?inst.id:'INST:ccu')+"'");
  s=rep1(s,'<div class="av">CC</div>','<div class="av">'+E(tb.av)+'</div>');
  s=rep1(s,'<div class="nm">California Credit Union</div>','<div class="nm">'+E(tb.name)+'</div>');
  s=rep1(s,'<div class="meta">NCUA #24980 · DFPI #9530137 · ~$1.3B</div>','<div class="meta">'+E(tb.meta)+'</div>');
  s=rep1(s,'<div class="val">445</div><div class="sub">across 16 object types</div>','<div class="val">'+o.total+'</div><div class="sub">across 16 object types</div>');
  s=rep1(s,'<div class="val">781</div><div class="sub">614 obligation links</div>','<div class="val">'+o.rel+'</div><div class="sub">'+o.oblig+' obligation links</div>');
  s=rep1(s,'id="kpi-attested">0%</div>','id="kpi-attested">'+o.attested+'%</div>');
  s=rep1(s,'<div class="val">68</div><div class="sub">NEEDS_FI items</div>','<div class="val">'+o.gaps+'</div><div class="sub">NEEDS_FI items</div>');
  s=rep1(s,'<div class="val">10</div><div class="sub">of 25 in library</div>','<div class="val">'+o.regpacks+'</div><div class="sub">of 25 in library</div>');
  const maxc=Math.max.apply(null,Object.values(o.counts))||1;
  COMP_ORDER.forEach(t=>{const lbl=COMP_TLABEL[t]||t,c=o.counts[t],w=Math.round(100*c/maxc),disp=c+((t==='Customer'||t==='Account')?'*':'');
    const re=new RegExp('(<span class="on">'+esc(lbl)+'</span><span class="bar"><i style="width:)[^"]*("></i></span><span class="oc">)[^<]*(</span>)');
    s=s.replace(re,(m,a,b,cc)=>a+w+'%'+b+disp+cc);});
  o.groups.forEach((grp,gi2)=>{const size=GROUPS[gi2][1],r=grp[1],p=grp[2],b=grp[3];const wr=Math.round(100*r/size),wp=Math.round(100*p/size),wb=Math.round(100*b/size);
    const re=new RegExp('(<span class="bg-name">'+esc(grp[0])+'</span><span class="bg-count">)[^<]*(</span></div><div class="sbar"><i class="r" style="width:)[^"]*("></i><i class="p" style="width:)[^"]*("></i><i class="b" style="width:)[^"]*(%?"></i>)');
    s=s.replace(re,(m,a,b2,c2,d2,e2)=>a+r+' ready · '+p+' partial · '+b+' blocked'+b2+wr+'%'+c2+wp+'%'+d2+(e2?wb:wb+'%')+e2);});
  const L=o.legend; s=s.replace(/Ready \(\d+\)/,'Ready ('+L[0]+')').replace(/Partial \(\d+\)/,'Partial ('+L[1]+')').replace(/Blocked \(\d+\)/,'Blocked ('+L[2]+')');
  const _acroN=(tb.name.split(/\s+/).filter(w=>/[A-Za-z]/.test(w[0]||'')).map(w=>w[0]).join('').toUpperCase().slice(0,5))||'FI';
  s=rep1(s,'<div class="lab">Agents ready</div><div class="val">6</div>','<div class="lab">Agents ready</div><div class="val">'+L[0]+'</div>');
  s=rep1(s,'<div class="lab">Partial</div><div class="val warn">23</div>','<div class="lab">Partial</div><div class="val warn">'+L[1]+'</div>');
  s=rep1(s,'<div class="lab">Blocked</div><div class="val">22</div>','<div class="lab">Blocked</div><div class="val">'+L[2]+'</div>');
  s=rethread(s,o.groups);
  s=rep1(s,'CCU is deposits-led consumer core, so front-office deposit &amp; service agents lead; lending, business and most efficiency agents are blocked until those modules load.',focusSentence(d.archetype||'',_acroN));
  const tr=pv.trace,pm=pv.meta;
  s=rep1(s,'<h3>Trace · Share Savings APY</h3><span class="hint">node PRC:share_savings</span>','<h3>Trace · '+E(tr.title)+'</h3><span class="hint">node '+E(tr.node)+'</span>');
  s=rep1(s,'<div class="ct">Source</div><div class="cv">Consumer Ratesheet</div><div class="cm">PDF · 03.02.26 · ccu.com</div>','<div class="ct">Source</div><div class="cv">'+E(tr.src_title)+'</div><div class="cm">'+E(tr.src_meta)+'</div>');
  s=rep1(s,'<div class="ct">Extracted field</div><div class="cv">"0.05% APY $100+"</div><div class="cm">daily balance, monthly</div>','<div class="ct">Extracted field</div><div class="cv">"'+E(tr.field)+'"</div><div class="cm">'+E(tr.field_meta)+'</div>');
  s=rep1(s,'<div class="ct">Graph node</div><div class="cv">Pricing · v0.9</div><div class="cm">confidence 0.85</div>','<div class="ct">Graph node</div><div class="cv">'+E(tr.gnode)+'</div><div class="cm">confidence '+(tr.conf!=null?tr.conf.toFixed(2):'—')+'</div>');
  s=rep1(s,'<div class="cv" style="color:var(--amber)">default-unconfirmed</div><div class="cm">awaiting FI sign-off</div>','<div class="cv" style="color:var(--amber)">'+E(tr.status)+'</div><div class="cm">awaiting FI sign-off</div>');
  s=rep1(s,'<div class="l">Owner</div><div class="v">Product / Finance</div>','<div class="l">Owner</div><div class="v">'+E(pm.owner)+'</div>');
  s=rep1(s,'<div class="l">Effective from</div><div class="v">2026-03-02</div>','<div class="l">Effective from</div><div class="v">'+E(pm.effective)+'</div>');
  s=rep1(s,'<div class="l">As-of (graph version)</div><div class="v">v1.2 · 2026-06-12</div>','<div class="l">As-of (graph version)</div><div class="v">'+E(pm.version)+'</div>');
  s=rep1(s,'<div class="l">PII classification</div><div class="v">none</div>','<div class="l">PII classification</div><div class="v">'+E(pm.pii)+'</div>');
  s=rep1(s,'<span class="hint">14 sources · last sync 2026-06-12</span>','<span class="hint">'+pv.nsrc+' sources · last sync '+E(pv.sync)+'</span>');
  let rows=pv.rows.map(r=>'<div class="lrow"><span class="fi-ic" style="background:'+r.col+'">'+r.icon+'</span><div><div class="lt">'+E(r.title)+'</div><div class="lm">'+E(r.meta)+'</div></div><span class="'+r.tag+'">'+E(r.cf)+'</span><span class="lm">'+E(r.date)+'</span></div>').join('');
  s=s.replace(/(<h3>Source register<\/h3>[\s\S]*?<div class="row-list">)[\s\S]*?(<\/div>\s*<\/section>)/,(m,a,b)=>a+rows+b);
  // revive JS-driven views (provenance search, gaps, sync) from inline graph
  s=s.split('JSON.parse(xhr.responseText)').join('(window.__KG||{nodes:{},edges:[]})');
  s=s.split('JSON.parse(__x.responseText)').join('(window.__KG||{nodes:{},edges:[]})');
  s=s.split('(xhr.status>=200&&xhr.status<400)||xhr.status===0').join('true');
  s=s.split('(__x.status>=200&&__x.status<400)||__x.status===0').join('true');
  s=s.split('var TOTAL=445').join('var TOTAL='+o.total);
  // sign-off queue KPIs (static CCU literals -> per-CU)
  const ready=o.total-o.gaps;
  s=rep1(s,'id="kpi-awaiting">445</div>','id="kpi-awaiting">'+o.total+'</div>');
  s=rep1(s,'<div class="lab">Your queue</div><div class="val">68</div>','<div class="lab">Your queue</div><div class="val">'+o.gaps+'</div>');
  s=rep1(s,'id="bulk-attest">Bulk attest DEP pack (124)','id="bulk-attest">Bulk attest ready set ('+ready+')');
  s=s.split("bulk.textContent='✓ DEP pack attested'").join("bulk.textContent='✓ ready set attested'");
  s=s.split("ratified+=124; update(); toast('DEP pack attested · 124 nodes ratified · deposit agents promoted')").join("ratified+="+ready+"; update(); toast('"+ready+" nodes ratified · agents promoted')");
  const tnode=(pv.trace&&pv.trace.node)||'PRC:share_savings';
  const prodId=(Object.values(g.nodes).find(n=>n.k==='prod')||{}).id||'';
  s=s.split("curId='PRC:share_savings'").join("curId='"+tnode+"'");
  s=s.split("'PRC:share_savings'").join("'"+tnode+"'");
  if(prodId)s=s.split("'PR:share_savings'").join("'"+prodId+"'");
  s=bindCards(s,d,o,tb.name,tb.av);
  const _acro=(tb.name.split(/\s+/).filter(w=>/[A-Za-z]/.test(w[0]||'')).map(w=>w[0]).join('').toUpperCase().slice(0,5))||'FI';
  s=s.split('\n').map(function(l){return l.indexOf('var G=')===0?l:l.split('California Credit Union').join(tb.name).split('California CU').join(tb.name).replace(/\bCCU\b/g,_acro);}).join('\n');
  return s;
}
global.KGEngine={convert,compute,topbar,provenance,buildPage};
})(typeof window!=='undefined'?window:globalThis);
