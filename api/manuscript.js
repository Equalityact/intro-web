'use strict';
const {parseManuscriptHtml,fetchDocumentHtml}=require('../lib/manuscript.cjs');
const known=require('../content/manuscript.json');
const config=require('../content/manuscript-source.json');
function createHandler({source=()=>process.env.MANUSCRIPT_DOC_HTML_URL || config.htmlUrl,fetchHtml=fetchDocumentHtml}={}) {
 return async function handler(req,res) {
  res.setHeader('Content-Type','application/json; charset=utf-8');res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Cache-Control','no-store');
  const send=(status,data)=>{res.statusCode=status;res.end(req.method==='HEAD'?undefined:JSON.stringify(data));};
  if(!['GET','HEAD'].includes(req.method)){res.setHeader('Allow','GET, HEAD');return send(405,{error:'METHOD_NOT_ALLOWED'});}
  try {const data=parseManuscriptHtml(await fetchHtml(source()),known);data.emphasis=known.reading_emphasis;res.setHeader('Cache-Control','public, max-age=0, s-maxage=60, stale-while-revalidate=60');return send(200,data);}
  catch {return send(503,{error:'MANUSCRIPT_UNAVAILABLE'});}
 };
}
module.exports=createHandler();module.exports.createHandler=createHandler;
