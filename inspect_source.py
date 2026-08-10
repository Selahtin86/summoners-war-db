import requests
from bs4 import BeautifulSoup

url='https://summonerswarskyarena.info/monster-list/'
r=requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=45)
r.raise_for_status()
html=r.text
for term in ['Darion','Colleen','Riley']:
    i=html.find(term)
    print('\n===== RAW', term, 'index', i, '=====')
    print(html[max(0,i-1200):i+1200])

soup=BeautifulSoup(html,'html.parser')
for row in soup.select('table tr'):
    if 'Darion' in row.get_text(' ', strip=True) or 'Darion' in str(row):
        print('\n===== DARION ROW PRETTIFY =====')
        print(row.prettify())
        break
