import tweepy
import pandas as pd
import os
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import requests
import random
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from apscheduler.schedulers.blocking import BlockingScheduler

CONSUMER_KEY = '<TWITTER_CONSUMER_KEY>'
CONSUMER_SECRET = '<TWITTER_CONSUMER_SECRET>'
ACCESS_KEY = '<TWITTER_ACCESS_KEY>'
ACCESS_SECRET = '<TWITTER_ACCESS_SECRET>'






scheduler = BlockingScheduler()

@scheduler.scheduled_job('interval', hours=8)
def executeBot():
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
    api = tweepy.API(auth)




    #Primero leo la informacion, una unica vez, ya que seria innecesario leer cada vez que se ejecuta una funciona
    if os.path.exists("full_data.csv"):
      os.remove("full_data.csv") #Para tener siempre la ultima version

    url = 'https://covid.ourworldindata.org/data/ecdc/full_data.csv'
    r = requests.get(url, allow_redirects=True)
    open('full_data.csv', 'wb').write(r.content)

    archivo = pd.read_csv('full_data.csv') #Leo con pandas el csv descargado


    def strtodate(fecha): #Convierte a datetime. Previa validacion de fechaValida
      formato = '%Y-%m-%d'
      return datetime.strptime(fecha , formato)



    startDate = strtodate('2020-03-01')
    today_date = datetime.today().strftime("%Y-%m-%d")
    endDate = strtodate(today_date)

    #Seleccionamos los paises
    primerPais = random.choice(archivo['location'])
    segundoPais = random.choice(archivo['location'])
    while primerPais == segundoPais:
        segundoPais = random.choice(archivo['location'])



    paises = []
    paises.append(primerPais)
    paises.append(segundoPais)
    total_cases = []
    total_deaths = []

    xDates = []
    dates = []
    cases = []
    yCases = []

    for pais in paises:
        countryRows = archivo[archivo['location'].str.lower() == pais.lower()]
        #Me quedo solo los que estan en el rango
        countryRows = (x for index, x in countryRows.iterrows() if (strtodate(x['date']) >= startDate and strtodate(x['date']) <= endDate))
        countryRows = pd.DataFrame(countryRows)
        datesCountry = countryRows['date'].tolist()
        for tempDate in datesCountry:
          if tempDate not in xDates:
            xDates.append(tempDate)
        dates.append(datesCountry)
        casosTotales = countryRows['total_cases'].tolist()
        cases.append(casosTotales)
        #Esta parte es solo para el tweet de los maximos
        total_cases.append(np.nanmax(casosTotales))
        total_deaths.append(np.nanmax(countryRows['total_deaths'].tolist()))

    xDates.sort()
    plt.figure(figsize=(14, 6)) #Inicio el grafico

    #Vamos pais x pais y agregamos los casos. Si no hubo fecha, no ponemos dato osea numpy.nan
    #print("X size: "+str(len(xDates)))
    i = 0
    while i < len(paises):
        newCases = []
        #Vamos fecha por fecha del total
        j = 0
        for xdate in xDates:
            if j >= len(dates[i]):
                newCases.append(np.nan)
            elif xdate == dates[i][j]:
                newCases.append(cases[i][j])
                j += 1
            else:
                newCases.append(np.nan)

        yCases.append(newCases)
        #print("newCases size: "+str(len(newCases)))
        i += 1

    i = 0
    while i < len(paises):
        #Ploteamos y usamos como eje X los dateTime de las fechas.
        #plt.plot(list(map(lambda x: strtodate(x) , dates)), cases[i], label=paises[i]) #Uso datetimes como eje X pues usando strings tenia problemas con el orden
        #list(map(lambda x: strtodate(x) , xDates))
        plt.plot(xDates, yCases[i], label=paises[i]) #Uso datetimes como eje X pues usando strings tenia problemas con el orden
        i += 1
    plt.xticks(rotation=60)
    xDatesTicks = []
    i = 0
    for tempDate in xDates:
        if i % 8 == 0:
            xDatesTicks.append(tempDate)
        else:
            xDatesTicks.append('')
        i += 1
    plt.xticks(xDatesTicks)
    #plt.margins(0.5)
    plt.legend() #le decimos a maplotlib que muestre todos los labels
    #plt.show()
    fileName = 'today_plot.png'
    plt.savefig(fileName)

    #Le agregamos watermark



    photo = Image.open(fileName)
    w, h = photo.size
    drawing = ImageDraw.Draw(photo)
    font = ImageFont.truetype('Roboto-Black.ttf', 16)
    text = 'tw: @infectionsbot'
    text_w, text_h = drawing.textsize(text, font)
    #pos = w - text_w*2, (h - text_h) - 100
    pos = 190, 140
    c_text = Image.new('RGB', (text_w, (text_h)), color = '#fff')
    c_text.putalpha(0)
    drawing = ImageDraw.Draw(c_text)
    drawing.text((0,0), text, fill="#b1b1b1", font=font)
    photo.paste(c_text, pos, c_text)
    photo.save(fileName)



    tweet_str = primerPais + ' VS ' + segundoPais + ' up to ' + today_date + '\n\n'
    tweet_str += primerPais + '\n    total cases: ' + str(int(total_cases[0]))
    tweet_str += '\n    total deaths: ' + str(int(total_deaths[0])) + '\n\n'
    tweet_str += segundoPais + '\n    total cases: ' + str(int(total_cases[1]))
    tweet_str += '\n    total deaths: ' + str(int(total_deaths[1])) + '\n\n'
    tweet_str += '#'+primerPais.replace(" ", "") + ' #'+segundoPais.replace(" ", "") + ' #covid19 #coronavirus'

    api.update_with_media(fileName, status=tweet_str)





#scheduler = BlockingScheduler()
#scheduler.add_job(executeBot, 'interval', hours=12)
scheduler.start()
print("Started...")
