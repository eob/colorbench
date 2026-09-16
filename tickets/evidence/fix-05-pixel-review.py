from collections import Counter,defaultdict
from functools import lru_cache
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'dataset/colorbench-v0.4.0'
if not D.exists(): D=ROOT/'dataset/candidate-rendered'
OLD=ROOT/'dataset/colorbench-v0.3.2'
rows=json.loads((D/'manifest.json').read_text())
old={r['taskId']:r for r in json.loads((OLD/'manifest.json').read_text())}
@lru_cache(maxsize=12)
def image(name,legacy=False):
 with Image.open((OLD if legacy else D)/name) as src:return src.convert('RGB')
def sha(data):return hashlib.sha256(data).hexdigest()
def reg(row):return {r['id']:r for r in row['rendered']['regions']}
def box(r):return(r['x'],r['y'],r['x']+r['width'],r['y']+r['height'])
def fill(im,b,color=(0,0,0)):
 x,y,x1,y1=b;ImageDraw.Draw(im).rectangle((x,y,x1-1,y1-1),fill=color)
def crop(row,label,legacy=False):return image(row['imageFilename'],legacy).crop(box(reg(row)[label]))
def groups(items,fn):
 out=defaultdict(list)
 for row in items:out[fn(row)].append(row)
 return out
report={'manifestSha256':sha((D/'manifest.json').read_bytes()),'taskCount':len(rows),'pngFiles':len({r['imageFilename'] for r in rows}),'findings':[]}
for r in rows:
 assert sha((D/r['imageFilename']).read_bytes())==r['imageSha256'],r['taskId']
 assert image(r['imageFilename']).size==(800,640)
report['allDeclaredImageHashesVerified']=True
# Fresh oracle uses full image plus complete prompt, hiding only the other patch.
report['onePatchCeilings']={}
for fam in ['samediff','lightness','chroma']:
 tests=[]
 for group,cell in groups([r for r in rows if r['family']==fam],lambda r:r['design'].get('pairSetId',r['design'].get('comparisonSetId'))).items():
  for direction,directed in groups(cell,lambda r:r['prompt']).items():
   for visible in 'AB':
    scores=defaultdict(Counter)
    for r in directed:
     im=image(r['imageFilename']).copy();fill(im,box(reg(r)['B' if visible=='A' else 'A']))
     scores[(sha(im.tobytes()),r['prompt'])][r['groundTruth']['choice']]+=1
    accuracy=sum(max(x.values()) for x in scores.values())/len(directed)
    assert accuracy==(.5 if fam=='samediff' else .625),(fam,group,visible,accuracy)
    tests.append(accuracy)
 report['onePatchCeilings'][fam]={'checks':len(tests),'minimum':min(tests),'maximum':max(tests)}
report['gradientSets']=[]
for name,cell in groups([r for r in rows if r['family']=='gradient'],lambda r:r['design']['optionSetId']).items():
 assert sorted(r['groundTruth']['choice'] for r in cell)==list('ABCD')
 options=[crop(cell[0],label) for label in 'ABCD']
 assert len({o.tobytes() for o in options})==4
 assert len({(o.crop((0,0,1,60)).tobytes(),o.crop((239,0,240,60)).tobytes()) for o in options})==1
 histograms=[Counter(o.getdata()) for o in options];assert all(h==histograms[0] for h in histograms)
 ceilings=[]
 for x in range(240):
  signatures=Counter(o.crop((x,0,x+1,60)).tobytes() for o in options)
  ceilings.append(len(signatures)/4)
  assert max(ceilings)<=.5
  assert all(n>=2 for n in signatures.values())
 for r in cell:
  assert crop(r,'R').tobytes()==crop(r,r['groundTruth']['choice']).tobytes()
  assert [crop(r,l).tobytes() for l in 'ABCD']==[o.tobytes() for o in options]
 gray=len({o.convert('L').tobytes() for o in options})==1
 assert gray==cell[0]['design']['grayscaleMatched']
 # A model deprived of target interiors retains both endpoints, options and all labels.
 masked=[]
 for r in cell:
  im=image(r['imageFilename']).copy(); rr=reg(r)['R'];fill(im,(rr['x']+1,rr['y'],rr['x']+rr['width']-1,rr['y']+rr['height']))
  masked.append((sha(im.tobytes()),r['prompt']))
 assert len(set(masked))==1
 report['gradientSets'].append({'set':name,'referenceCount':4,'width':240,'endpointCeiling':ceilings[0],'maxFixedColumnCeiling':max(ceilings),'grayscaleIdentical':gray})
assert sum(g['grayscaleIdentical'] for g in report['gradientSets'])==2
report['interventions']={}
NEUTRAL=(238,238,238)
for fam in ['context','smallmatch']:
 checks=0
 family=[r for r in rows if r['family']==fam]
 for name,cell in groups(family,lambda r:r['groupId']).items():
  outside=[]; signatures=[]
  assert len({r['prompt'] for r in cell})==1
  assert len({json.dumps(r['groundTruth']) for r in cell})==1
  for r in cell:
   rr=reg(r); im=image(r['imageFilename']).copy();d=r['design']
   colors={l:crop(r,l).getpixel((0,0)) for l in 'RABCD'}
   palette=int(d['interventionSetId'].rsplit('-',1)[1])-1
   position='ABCD'.index(r['groundTruth']['choice'])
   prior=old[f'colorbench-{fam}-{palette*4+position+1:02d}']
   assert colors=={l:crop(prior,l,True).getpixel((0,0)) for l in 'RABCD'},r['taskId']
   signatures.append(tuple((l,colors[l],rr[l]['x']*2+rr[l]['width'],rr[l]['y']*2+rr[l]['height']) for l in 'RABCD'))
   for l in 'RABCD':
    x,y,x1,y1=box(rr[l]); actual=crop(r,l)
    if fam=='context':
     assert actual.size==(84,84) and len(actual.getcolors())==1
     if l!='R':
      color=tuple(d['surround'][l]); ringboxes=[(x-12,y-12,x1+12,y),(x-12,y1,x1+12,y1+12),(x-12,y,x,y1),(x1,y,x1+12,y1)]
      for b in ringboxes:
       assert im.crop(b).getcolors()==[(im.crop(b).width*im.crop(b).height,color)]
       fill(im,b)
    else:
     cx=(x+x1)//2;cy=(y+y1)//2;maximum=(cx-42,cy-42,cx+42,cy+42)
     expected=Image.new('RGB',(84,84),NEUTRAL);draw=ImageDraw.Draw(expected)
     size=d['sizePx'];offset=(84-size)//2;draw.rectangle((offset,offset,offset+size-1,offset+size-1),fill=colors[l])
     if d['strokePx']:
      stroke=d['strokePx'];draw.rectangle((stroke,stroke,83-stroke,83-stroke),fill=NEUTRAL)
     assert im.crop(maximum).tobytes()==expected.tobytes(),r['taskId']
     fill(im,maximum)
   outside.append(sha(im.tobytes()));checks+=1
  assert len(set(outside))==1,(fam,name,'outside mismatch')
  assert len(set(signatures))==1,(fam,name,'color/center mismatch')
 # Surround condition arrays stay identical across reference changes and cross every position.
 if fam=='context':
  for palette,rs in groups(family,lambda r:r['design']['interventionSetId']).items():
   arrays={}
   for condition,cs in groups(rs,lambda r:r['design']['condition']).items():
    arrays[condition]=[tuple(image(r['imageFilename']).getpixel((reg(r)[l]['x']-1,reg(r)[l]['y']-1)) for l in 'ABCD') for r in cs]
    assert len(set(arrays[condition]))==1
   assert arrays['neutral'][0]==(NEUTRAL,)*4
   base=arrays['surround-0'][0]
   assert len(set(base))==4
   for i in range(4):assert arrays[f'surround-{i}'][0]==base[i:]+base[:i]
 report['interventions'][fam]={'matchedReferenceGroups':len(groups(family,lambda r:r['groupId'])),'renderedConditionsChecked':checks,'original032ColorsPreserved':True,'outsideInterventionPixelsIdentical':True,'fullMaximumSmallRegionFootprintValidated':fam=='smallmatch'}
retained=[r for r in rows if r['family'] in ['matching','binding','hue','rgb','hsl','oklch']]
assert all(image(r['imageFilename']).tobytes()==image(old[r['taskId']]['imageFilename'],True).tobytes() for r in retained)
report['retained032ImagesPixelIdentical']=len(retained)
(ROOT/'tickets/evidence/fix-05-pixel-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
