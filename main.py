from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import slackweb

Url="https://www.keibalab.jp/db/jockey/05212/"
html = urlopen(Url)
bsObj = BeautifulSoup(html,"html.parser")

#テーブルを指定
table = bsObj.find('table', id="20180811")
tables = pd.read_html(Url)
doyou =tables[3]
#距離の１文字目と以降に分割
doyou['芝ダ'] = doyou[['コース']].apply(lambda x: x[0][0], axis=1)
doyou['コース'] = doyou[['コース']].apply(lambda x: x[0][1:], axis=1).astype("int64")
#抽出条件
doyou = doyou[doyou['コース']>=1800]
links = ["https://www.keibalab.jp"+x.get("href")+"umabashira.html"  for x in table.find_all("a") if x.get("itemprop")=="url"]
links = [s for s in links if 'race' in s]

df_tan_nin = pd.DataFrame(columns=["単勝","人気"])

for i in doyou.index:
    html = urlopen(links[i])
    bsObj = BeautifulSoup(html,"html.parser")
    megamoriTable =bsObj.findAll("table",{"class":"megamoriTable"})[0]
    rows = megamoriTable.findAll('tr', attrs={'class': "seirei std9"})
    tds = rows[1].findAll('td')
    td_no = 18 - doyou["馬"][i]
    tan_ninki=tds[td_no].get_text().replace('\n','').replace('\t','').replace(' ','')
    tansho = re.split('[()]', tan_ninki)[0]
    ninki = re.split('[()]', tan_ninki)[1]
    df_tan_nin = df_tan_nin.append(pd.DataFrame([[tansho, ninki]],columns=["単勝","人気"], index=[i]))
    #print(tansho,",",ninki)
    time.sleep(1)

slack = slackweb.Slack(url=WEBHOOK_URL)
slack.notify(text="条件に合致するレースを報告します")    
for i in doyou.index:
    slack.notify(text="第"+str(doyou['R'][i])+"レース"+str(doyou['レース名'][i])+"が"+df_tan_nin["人気"][i]+"番人気で、"
                 +"単勝は"+df_tan_nin["単勝"][i]+"です")