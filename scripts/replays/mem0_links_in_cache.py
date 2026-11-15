"""Count the links (linked_memory_ids) in Mem0's cached extraction replies.
Run from the top of agent-memory-eval: python3 <this file>. No model calls."""
import json, glob
tot=0; withlinks=0; mems=0; linked=0; rows=[]
for f in glob.glob('.cache/llm/*/*.json'):
    raw=open(f).read()
    if 'attributed_to' not in raw: continue
    try:
        rep=json.loads(raw)
        if isinstance(rep,str): rep=json.loads(rep)
        content=rep['choices'][0]['message']['content']
        out=json.loads(content[content.find('{'):content.rfind('}')+1], strict=False)
    except Exception as e:
        continue
    ms=out.get('memory')
    if not isinstance(ms,list): continue
    tot+=1; mems+=len(ms)
    l=[m for m in ms if isinstance(m,dict) and m.get('linked_memory_ids')]
    linked+=len(l); withlinks+=bool(l)
    rows.append((f,ms))
print('extraction replies',tot,'with >=1 link',withlinks,'memories',mems,'linked memories',linked)
for needle in ['five sessions of a bereavement','7:30 am','nearing 1300','close to 1300','Oahu','every other week','shoe rack']:
    for f,ms in rows:
        for m in ms:
            if isinstance(m,dict) and needle in m.get('text',''):
                print('\n##',needle,'|',f[-12:]); print(json.dumps(m)[:500])
