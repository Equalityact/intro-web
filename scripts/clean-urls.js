// live-server 미들웨어: /resources 처럼 확장자 없는 주소를 resources.html로 연결하고,
// /resources.html 로 들어오면 /resources 로 돌려보냅니다.
const fs = require('fs');
const path = require('path');
const envFile = path.resolve(__dirname, '..', '.env');
if (fs.existsSync(envFile)) process.loadEnvFile(envFile);
const timeline = require('../api/timeline');

const root = path.resolve(__dirname, '..', 'public');

module.exports = function cleanUrls(req, res, next) {
  const [pathname, query = ''] = req.url.split('?');
  const qs = query ? '?' + query : '';
  if (pathname === '/api/timeline') {
    timeline(req, res).catch(next);
    return;
  }

  if (pathname.endsWith('.html')) {
    const clean = pathname === '/index.html' ? '/' : pathname.slice(0, -5);
    res.statusCode = 301;
    res.setHeader('Location', clean + qs);
    return res.end();
  }
  if (pathname !== '/' && !path.extname(pathname)) {
    const file = path.join(root, pathname.replace(/\/$/, '') + '.html');
    if (file.startsWith(root) && fs.existsSync(file)) req.url = pathname.replace(/\/$/, '') + '.html' + qs;
  }
  next();
};
