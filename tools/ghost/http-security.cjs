"use strict";
const SECURITY_HEADERS=Object.freeze({
 'X-Content-Type-Options':'nosniff',
 'Referrer-Policy':'no-referrer',
 'Cache-Control':'no-store',
 'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-src https://www.tradingview-widget.com; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
 'X-Frame-Options':'DENY',
 'Permissions-Policy':'camera=(), microphone=(), geolocation=()',
 'Strict-Transport-Security':'max-age=31536000',
});
function sameOrigin(req,origin){
 return !!origin&&req.headers.origin===origin&&(!req.headers['sec-fetch-site']||req.headers['sec-fetch-site']==='same-origin');
}
module.exports={SECURITY_HEADERS,sameOrigin};
