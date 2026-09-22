import json,pandas as pd,streamlit as st
from .database import init_db,search,get,stats
from .processing import process,OCR
init_db(); st.set_page_config(page_title='Document Intelligence',layout='wide')
st.title('AI-Powered Multi-Document Intelligence')
st.caption('Working MVP: upload, OCR, classification, extraction, validation, storage and search')
page=st.sidebar.radio('Navigation',['Dashboard','Upload & Process','Document Search','Document Viewer'])
st.sidebar.write('OCR:', 'Available' if OCR else 'Not detected')
if page=='Dashboard':
 total,types=stats(); a,b,c=st.columns(3); a.metric('Documents Processed',total); b.metric('Document Types',len(types)); c.metric('Working Modules','9')
 st.subheader('Document Distribution')
 if types:
  df=pd.DataFrame([dict(x) for x in types]); st.bar_chart(df.set_index('document_type')['n']); st.dataframe(df,use_container_width=True,hide_index=True)
 else: st.info('Upload documents to begin.')
 st.subheader('Current Pipeline'); st.code('Upload\n  ↓\nPreprocessing\n  ↓\nOCR / Text Extraction\n  ↓\nClassification\n  ↓\nInformation Extraction\n  ↓\nValidation\n  ↓\nSQLite Repository\n  ↓\nSearch / Retrieval')
elif page=='Upload & Process':
 st.header('Upload and Process Documents'); fs=st.file_uploader('Upload one or multiple PDF/JPG/PNG files',type=['pdf','png','jpg','jpeg'],accept_multiple_files=True)
 if fs and st.button('Process Documents',type='primary'):
  rows=[]; p=st.progress(0)
  for i,f in enumerate(fs):
   try:
    iD,r=process(f); v=json.loads(r['validation_json']); rows.append({'ID':iD,'File':r['filename'],'Type':r['document_type'],'Pages':r['page_count'],'Status':v['status']})
   except Exception as e: rows.append({'ID':'-','File':f.name,'Type':'Error','Pages':'-','Status':str(e)})
   p.progress((i+1)/len(fs))
  st.success(f'Processed {len(fs)} document(s).'); st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
elif page=='Document Search':
 st.header('Intelligent Document Search'); q=st.text_input('Search filename, text, vendor, amount, GST number, etc.'); typ=st.selectbox('Document type',['All','Invoice','Receipt','Purchase Order','Contract','KYC','Form','Unknown']); rows=search(q,typ); st.write('Results:',len(rows))
 if rows:
  out=[]
  for r in rows:
   f=json.loads(r['fields_json'] or '{}'); v=json.loads(r['validation_json'] or '{}'); out.append({'ID':r['id'],'Filename':r['filename'],'Type':r['document_type'],'Date':f.get('date',''),'Vendor':f.get('vendor',''),'Amount':f.get('total_amount',''),'Status':v.get('status','')})
  df=pd.DataFrame(out); st.dataframe(df,use_container_width=True,hide_index=True); st.download_button('Export CSV',df.to_csv(index=False).encode(),'document_results.csv','text/csv')
 else: st.info('No matching documents found.')
elif page=='Document Viewer':
 st.header('Document Viewer'); rows=search()
 if not rows: st.info('No documents available.')
 else:
  opts={f"{r['id']} — {r['filename']}":r['id'] for r in rows}; choice=st.selectbox('Select document',list(opts)); r=get(opts[choice]); f=json.loads(r['fields_json'] or '{}'); v=json.loads(r['validation_json'] or '{}')
  a,b,c=st.columns(3); a.metric('Type',r['document_type']); b.metric('Pages',r['page_count']); c.metric('Validation',v.get('status','Unknown'))
  st.subheader('Extracted Information'); st.dataframe(pd.DataFrame([{'Field':k.replace('_',' ').title(),'Value':v} for k,v in f.items()]),use_container_width=True,hide_index=True)
  if v.get('issues'):
   st.warning('Validation issues'); [st.write('- '+x) for x in v['issues']]
  st.subheader('Extracted Text'); st.text_area('OCR / PDF text',r['extracted_text'] or 'No text extracted.',height=350)
  st.download_button('Download JSON',json.dumps({'document':r['filename'],'type':r['document_type'],'fields':f,'validation':v,'text':r['extracted_text']},indent=2,ensure_ascii=False).encode(),f'document_{r["id"]}.json','application/json')
