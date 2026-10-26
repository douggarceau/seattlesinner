# wrap the artifact page into a standalone index.html
import sys,re
src=open(sys.argv[1]).read()
# if it's the live artifact file (has the platform skeleton), strip it
m=re.match(r'\s*<!doctype html><html><head>.*?</head><body>\n?',src,re.S|re.I)
if m: src=src[m.end():]
src=re.sub(r'</body></html>\s*$','',src)
head='''<!doctype html>
<html lang="en">
<head>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-4V8SL4DPMW"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-4V8SL4DPMW');</script>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="The Guitar Doug Report: bars, clubs, local music, the alternative scene and the stories nobody else will run.">
<meta property="og:title" content="The Guitar Doug Report">
<meta property="og:description" content="Bars, clubs, local music, the alternative scene and the stories nobody else will run.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://seattlesinner.com/">
<meta property="og:site_name" content="The Guitar Doug Report">
<meta property="og:image" content="https://seattlesinner.com/report/masthead.png">
<meta property="og:image:secure_url" content="https://seattlesinner.com/report/masthead.png">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="The Guitar Doug Report">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="The Guitar Doug Report">
<meta name="twitter:description" content="Bars, clubs, local music, the alternative scene and the stories nobody else will run.">
<meta name="twitter:image" content="https://seattlesinner.com/report/masthead.png">
<link rel="canonical" href="https://seattlesinner.com/">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%94%A5%3C/text%3E%3C/svg%3E">
<style>[hidden]{display:none!important}body{margin:0}</style>
</head>
<body>
'''
open(sys.argv[2],'w').write(head+src+'\n</body>\n</html>\n')
