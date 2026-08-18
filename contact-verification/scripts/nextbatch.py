import json,urllib.parse,sys
n=int(sys.argv[1]) if len(sys.argv)>1 else 6
done={x['id'] for x in json.load(open('li_verdicts.json'))}
q=[r for r in json.load(open('queue_li.json')) if r['id'] not in done]
print(f"REMAINING {len(q)}")
for r in q[:n]:
    print(r['id'],'|',r['n'],'|',r['co'],'|',r['jt'],'|',urllib.parse.quote(r['ident'].split('?')[0]))
