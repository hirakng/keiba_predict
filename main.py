from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import slackweb
import os
import datetime


#次のレース日付を計算
now = datetime.datetime.now()
nextSaturday= now + datetime.timedelta(days=5-now.weekday())
nextSunday = now + datetime.timedelta(days=6-now.weekday())
id = [nextSaturday.strftime('%Y%m%d'),nextSunday.strftime('%Y%m%d')]
youbi=["土曜","日曜"]
jockey=["デムーロ","ルメール"]
Url=["https://www.keibalab.jp/db/jockey/05212/","https://www.keibalab.jp/db/jockey/05339/"]


def preprocessed(tables,weekday):
    #weekday=0：土曜、１：日曜
    if weekday==0:
        daytable =tables[3]
    else:
        daytable = tables[4]
    #距離の１文字目と以降に分割
    daytable['芝ダ'] = daytable[['コース']].apply(lambda x: x[0][0], axis=1)
    daytable['コース'] = daytable[['コース']].apply(lambda x: x[0][1:], axis=1).astype("int64")
    return daytable
def extraction(daytable):
    daytable = daytable[daytable['コース']>2000]
    return daytable

def getLinks(table):
    links = ["https://www.keibalab.jp"+x.get("href")+"umabashira.html"  for x in table.find_all("a") if x.get("itemprop")=="url"]
    links = [s for s in links if 'race' in s]
    return links
def getTanNin(daytable,links):
    df_tan_nin = pd.DataFrame(columns=["単勝","人気"])
    for i in daytable.index:
        html = urlopen(links[i])
        bsObj = BeautifulSoup(html,"html.parser")
        megamoriTable =bsObj.findAll("table",{"class":"megamoriTable"})[0]
        rows = megamoriTable.findAll('tr', attrs={'class': "seirei std9"})
        tds = rows[1].findAll('td')
        td_no = 18 - daytable["馬"][i]
        tan_ninki=tds[td_no].get_text().replace('\n','').replace('\t','').replace(' ','')
        if tan_ninki!="":
            tansho = re.split('[()]', tan_ninki)[0]
            ninki = re.split('[()]', tan_ninki)[1]
        else:
            tansho = "xx"
            ninki = "xx"
        df_tan_nin = df_tan_nin.append(pd.DataFrame([[tansho, ninki]],columns=["単勝","人気"], index=[i]))
        #print(tansho,",",ninki)
        time.sleep(1)
    return df_tan_nin

def slackout(daytable,df_tan_nin,jockey,youbi):
    slack = slackweb.Slack(url=os.environ.get('WEBHOOK_URL'))
    if len(df_tan_nin)==0:
        slack.notify(text="*"+jockey+"の"+youbi+"のレースで条件に合致するものはありません:racehorse:"+"*",mrkdwn= True)    
    else:
        slack.notify(text="*"+jockey+"の"+youbi+"のレースで条件に合致するものを報告します:racehorse:"+"*",mrkdwn= True)    
        for i in daytable.index:
            slack.notify(text="第"+str(daytable['R'][i])+"レース"+str(daytable['レース名'][i])+str(daytable['コース'][i])+"ｍが"+df_tan_nin["人気"][i]+"番人気で、"
                        +"単勝は"+df_tan_nin["単勝"][i]+"です")
#金、土、日のみ実行         
if now.weekday() in [4,5,6]:
    #メイン（デムーロ、ルメール）
    for j in range(2):
        html = urlopen(Url[j])
        bsObj = BeautifulSoup(html,"html.parser")

        #土曜、日曜でループ
        for i in range(2):
            #テーブルを指定
            table = bsObj.find('table', id=id[i])

            if table != None:
                #次のレーステーブルがあれば実行
                tables = pd.read_html(Url[j])
                daytable = preprocessed(tables,i)
                #抽出条件
                daytable = extraction(daytable)
                #レースのリンクを取得
                links = getLinks(table)
                #リンク先から人気・単勝を取得
                if daytable['馬'].isnull().any()==False:
                    df_tan_nin = getTanNin(daytable,links)
                    slackout(daytable,df_tan_nin,jockey[j],youbi[i])
                else:
                    if i==0:
                        slack = slackweb.Slack(url=os.environ.get('WEBHOOK_URL'))
                        slack.notify(text="馬番決定前です")    
            else:
                if i==0:
                    slack = slackweb.Slack(url=os.environ.get('WEBHOOK_URL'))
                    slack.notify(text="翌週のレース情報がまだ出てません")
            time.sleep(5)


