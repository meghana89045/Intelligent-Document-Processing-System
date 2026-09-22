import io,re,json
from pathlib import Path
from datetime import datetime
import fitz, cv2, numpy as np
from PIL import Image
try:
 import pytesseract; OCR=True
except Exception: OCR=False
from .config import UPLOAD_DIR
from .database import insert

KEYS={'Invoice':['invoice','tax invoice','subtotal','gst','bill to'],'Receipt':['receipt','payment received','paid','transaction'],'Purchase Order':['purchase order','po number','supplier','order date'],'Contract':['agreement','contract','terms and conditions','effective date'],'KYC':['kyc','date of birth','aadhaar','passport','identity'],'Form':['application form','applicant','signature','declaration']}

def prep(im):
 a=np.array(im.convert('RGB')); g=cv2.cvtColor(a,cv2.COLOR_RGB2GRAY); g=cv2.GaussianBlur(g,(3,3),0); _,t=cv2.threshold(g,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU); return Image.fromarray(t)
def ocr(im):
 if not OCR:return ''
 try:return pytesseract.image_to_string(prep(im))
 except:return ''
def extract(data,suf):
 if suf=='.pdf':
  d=fitz.open(stream=data,filetype='pdf'); out=[]
  for pg in d:
   t=pg.get_text('text')
   if t.strip(): out.append(t)
   elif OCR:
    pix=pg.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False); out.append(ocr(Image.open(io.BytesIO(pix.tobytes('png')))))
  return '\n'.join(out),len(d)
 return ocr(Image.open(io.BytesIO(data))),1
def classify(t):
 l=t.lower(); scores={k:sum(x in l for x in v) for k,v in KEYS.items()}; b=max(scores,key=scores.get); return b if scores[b] else 'Unknown'
def match(t, pats):
 for p in pats:
  m=re.search(p,t,re.I|re.M)
  if m:return m.group(1).strip()
 return ''
def fields(t,typ):
 f={}
 if typ in ('Invoice','Receipt','Purchase Order'):
  f['document_number']=match(t,[r'(?:invoice\s*(?:no|number|#)|inv\s*(?:no|#)|receipt\s*(?:no|number|#)|po\s*(?:no|number|#))\s*[:\-]?\s*([A-Z0-9][A-Z0-9/\-]*)'])
  f['date']=match(t,[r'(?:invoice\s*date|date|order\s*date)\s*[:\-]?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})'])
  f['vendor']=match(t,[r'(?:vendor|supplier|seller|from)\s*[:\-]\s*([^\n]+)'])
  f['gst_number']=match(t,[r'\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z])\b'])
  a=match(t,[r'(?:grand\s*total|total\s*amount|invoice\s*total|total)\s*[:\-]?\s*(?:₹|rs\.?|inr)?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)']); f['total_amount']=a.replace(',','') if a else ''
  x=match(t,[r'(?:gst|tax|cgst|sgst)\s*[:\-]?\s*(?:₹|rs\.?|inr)?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)']); f['tax_amount']=x.replace(',','') if x else ''
 else: f['name']=match(t,[r'(?:name|customer|applicant|party)\s*[:\-]\s*([^\n]+)'])
 return f
def validate(f,t,typ):
 issues=[]
 if not t.strip():issues.append('No text extracted; OCR may be unavailable or document unreadable.')
 if typ in ('Invoice','Receipt','Purchase Order'):
  for k,label in [('document_number','document number'),('date','date'),('total_amount','total amount')]:
   if not f.get(k):issues.append(f'{label.title()} not detected.')
  try:
   if float(f.get('tax_amount') or 0)>float(f.get('total_amount') or 0):issues.append('Tax amount exceeds total amount; verify extraction.')
  except:pass
 return {'status':'Needs Review' if issues else 'Validated','issues':issues}
def process(file):
 data=file.getvalue(); suf=Path(file.name).suffix.lower(); UPLOAD_DIR.mkdir(parents=True,exist_ok=True); target=UPLOAD_DIR/(datetime.now().strftime('%Y%m%d%H%M%S%f')+'_'+re.sub(r'[^A-Za-z0-9._-]','_',file.name)); target.write_bytes(data)
 text,pages=extract(data,suf); typ=classify(text); f=fields(text,typ); v=validate(f,text,typ)
 r={'filename':file.name,'stored_path':str(target),'document_type':typ,'upload_time':datetime.now().isoformat(timespec='seconds'),'page_count':pages,'extracted_text':text,'fields_json':json.dumps(f,ensure_ascii=False),'validation_json':json.dumps(v,ensure_ascii=False)}
 return insert(r),r
