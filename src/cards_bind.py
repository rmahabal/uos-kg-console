import re, html as _h
E=_h.escape
def bind_cards(s, d, o, name, av, cards):
    cd=cards(d)
    arch=(cd['archetype'] or '').lower()
    charter='Federal' if ('federal' in arch or ' fcu' in arch) else ('State-chartered' if 'state' in arch else 'Chartered')
    focus='lending-led' if 'lending' in arch else ('commercial' if 'commercial' in arch else 'deposits-led')
    archlabel=charter+' · '+focus
    acro=''.join(w[0] for w in name.split() if w[:1].isalpha()).upper()[:5] or E(av)
    s=s.replace('<title>Knowledge Graph Console · California CU · UOS</title>','<title>Knowledge Graph Console · '+E(name)+' · UOS</title>')
    s=s.replace('<span class="pill">State-chartered · deposits-led</span>','<span class="pill">'+E(archlabel)+'</span>')
    # attestation
    s=s.replace('<div class="big"><b>0 / 445</b><span>nodes attested by CCU</span></div>','<div class="big"><b>0 / '+str(cd['total'])+'</b><span>nodes attested by '+E(acro)+'</span></div>')
    s=s.replace('Source confidence (avg 0.66)','Source confidence (avg '+('%.2f'%cd['avg'])+')')
    s=s.replace('0.85+ · 68','0.85+ · '+str(cd['b1']))
    s=s.replace('0.70–0.84 · 49','0.70–0.84 · '+str(cd['b2']))
    s=s.replace('0.50–0.69 · 327','0.50–0.69 · '+str(cd['b3']))
    s=s.replace('&lt;0.5 · 1','&lt;0.5 · '+str(cd['b4']))
    # reg coverage
    s=s.replace('<h3>Regulatory coverage</h3><span class="more">10 / 25 packs</span>','<h3>Regulatory coverage</h3><span class="more">'+str(o['regpacks'])+' / 25 packs</span>')
    pills=''.join('<span class="chip on">'+E(p)+'</span>' for p in cd['packs'])
    s=s.replace('<div class="chips" style="margin-bottom:12px"><span class="chip on">DEP</span><span class="chip on">CIP-BSA</span><span class="chip on">PRIV-SEC</span><span class="chip on">FRAUD</span><span class="chip on">SERV-DEP</span><span class="chip on">DISPUTES</span><span class="chip on">CONS-COMPLIANCE</span><span class="chip on">PAY</span><span class="chip on">CARDS</span><span class="chip on">COMMS</span></div>','<div class="chips" style="margin-bottom:12px">'+pills+'</div>')
    s=s.replace('15 more in the 25-pack library · not yet loaded',str(cd['more'])+' more in the 25-pack library · not yet loaded')
    s=s.replace('CCU is a deposits-led consumer core.',E(acro)+' is a '+focus+' institution.')
    # recent activity
    s=s.replace('Graph composed — 445 nodes, 781 edges','Graph composed — '+str(cd['total'])+' nodes, '+str(cd['rel'])+' edges')
    s=s.replace('10 reg packs seeded · 614 obligations wired 1:1',str(o['regpacks'])+' reg packs seeded · '+str(cd['oblig'])+' obligations wired 1:1')
    packsumm=', '.join(cd['packs'][:3])+((' … '+cd['packs'][-1]) if len(cd['packs'])>3 else '')
    s=s.replace('DEP, CIP-BSA, PRIV-SEC … COMMS',E(packsumm))
    s=s.replace('68 items flagged NEEDS_FI',str(cd['gaps'])+' items flagged NEEDS_FI')
    # top gaps (regenerate items inside the card)
    gh=''.join('<div class="gap"><div class="gt">'+E(t)+' <span class="gm">— '+E(h)+'</span></div><span class="gb">blocks '+str(b)+' agents</span></div>' for t,h,b in cd['topgaps']) or '<div class="gap"><div class="gt">No open gaps — all knowledge present</div></div>'
    s=re.sub(r'(Top gaps to close · NEEDS_FI</h3>.*?<div>)(.*?)(</div>\s*</section>)', lambda m: m.group(1)+gh+m.group(3), s, count=1, flags=re.S)
    return s
