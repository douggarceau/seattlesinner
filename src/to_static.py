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
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="Seattle Sinner: bars, clubs, local music, the alternative scene and the stories nobody else will run.">
<meta property="og:title" content="Seattle Sinner">
<meta property="og:description" content="Bars, clubs, local music, the alternative scene and the stories nobody else will run.">
<meta property="og:type" content="website">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%94%A5%3C/text%3E%3C/svg%3E">
<style>[hidden]{display:none!important}body{margin:0}</style>
</head>
<body>
'''
open(sys.argv[2],'w').write(head+src+'\n</body>\n</html>\n')
