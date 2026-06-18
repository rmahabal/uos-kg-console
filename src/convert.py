"""instance KG JSON  ->  Explorer 'web G' format. Reproduces web-bundle/ccu_graph.json."""
import json

TYPE2K = {  # instance node-type -> explorer k-code
 'Institution':'inst','Product':'prod','Feature':'feat','Segment':'seg','Channel':'chan',
 'RuleThreshold':'rule','Pricing':'price','Authority':'auth','Policy':'pol','Disclosure':'disc',
 'DocumentRequirement':'doc','OfferPromotion':'offer','Consent':'cons','Source':'src',
 'Customer':'cust','Account':'acct',
}
KL = {'inst':'Institution','prod':'Product','feat':'Feature','seg':'Segment','chan':'Channel',
 'rule':'Rule','price':'Pricing','auth':'Authority','pol':'Policy','disc':'Disclosure',
 'doc':'Doc Req','offer':'Offer','cons':'Consent','src':'Source','cust':'Customer','acct':'Account'}
# per-type 'field' (headline extracted value)
FIELD = {'inst':'legal_name','prod':'features','feat':'type','seg':'definition_criteria',
 'chan':'description','rule':'condition','price':'apy_summary','auth':'action','pol':'domain',
 'disc':'type','doc':'applicant_type','offer':'incentive','cons':'name','src':'description'}

def _field(k, n):
    f = FIELD.get(k)
    if not f: return n.get('name','')
    v = n.get(f)
    if isinstance(v, list): return ', '.join(str(x) for x in v)
    return v if v is not None else (n.get('name','') or '')

def convert_instance(d):
    nodes = {}
    for t, arr in d.get('nodes', {}).items():
        k = TYPE2K.get(t, t.lower())
        for n in arr:
            prov = n.get('source_provenance') or {}
            conf = n.get('confidence_score')
            srcn = prov.get('source', '')
            nodes[n['id']] = {
                'id': n['id'], 'k': k, 'kl': KL.get(k, t),
                'name': n.get('name') or ' '.join(w.capitalize() for w in n['id'].split(':',1)[-1].replace('_',' ').split()),
                'nf': False,
                'conf': conf,
                'src': (f"{srcn} · conf {conf}" if srcn else ''),
                'ver': n.get('version'),
                'eff': n.get('effective_from'),
                'effto': n.get('effective_to') or '—',
                'owner': n.get('owner'),
                'pii': n.get('pii_classification'),
                'st': n.get('state'),
                'url': prov.get('url', ''),
                'cls': prov.get('class', ''),
                'srcn': srcn,
                'field': _field(k, n),
            }
    edges = [[e['from'], e['to'], e['rel']] for e in d.get('edges', [])]
    return {'nodes': nodes, 'edges': edges}

if __name__ == '__main__':
    import sys
    g = convert_instance(json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'data/ccu.json')))
    print('nodes:', len(g['nodes']), 'edges:', len(g['edges']))
