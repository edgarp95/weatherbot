#!/usr/bin/env python
# coding: utf-8

# Fail, mida võib muuta ja mis tuleb esitada koduse töö lahendusena
# Faili nime peab jätma samaks
# Faili võib muuta suvaliselt, kuid see peab sisaldama funktsiooni getResponse(),
# millele antakse argumendina ette kasutajalt sisendiks saadud tekst (sõnena)
# ja mis tagastab sobiva vastuse (samuti sõnena)
import urllib.request
import json
import re
from datetime import timedelta
import datetime
import unicodedata
# See vajalik boonusülesande jaoks
from googletrans import Translator  # seda peab installeerima!!!

username = "Kasutaja"  # kasutaja esialgne nimi, kui kasutaja ei muuda seda, see ka jääb!
# flag, mis näitab, kas me alles alustasime suhtlust, vajalik linnanimede ja sõnastike sisse lugemiseks
first_time = True
cities = []  # siia loeme kõik linnad, mida api oskab töödelda

# api vastus üldiselt ilma kohta, need 4 on need, mida ma leidsin, seega kui tekib mingi uus, siis võib error tulla!
eng_est_dict = {  # see on sõna otseses mõttes sõnastik ;)
    "Clouds": "pilvine",
    "Clear": "selge",
    "Mist": "udune",
    "Rain": "vihmane",
    "Fog": "udune",
    "Snow": "lumine"
}
# tuulesõnastik, siia kogume võimalikud kraadid ning neile vastva nimetuse: nt 360 kraadi - põhjatuul
wind_dict = {}


# peamine tagastav meetod
def getResponse(text):
    global first_time

    # Kui jutt bottiga alles algas, loeme sisse linnad ja tuulesuunad
    if first_time:
        readInCities()
        readInWindDict()
        first_time = False

    # kasutaja tekstist võtame välja kõik enam-võimalikud kirjavahemärgid
    stripped_text = text.strip(".;,!?")

    # tagastame boti vastuse
    return textAnalyzer(stripped_text)


# see loeb meil linnad failist cities muutujasse
def readInCities():
    global cities
    with open("cities.txt", encoding="utf8") as f:
        cities = f.readlines()

    # cities = [x.strip().lower() for x in cities]
    # Esialgu kasutasime kõiki linnu väikse tähega, aga kuna ülesande tingimuses kirjas, et linn on suure tähega,
    # siis muudame seda, peale selle väikse tähega,
    # linnade puhul tekkib tihti segadus eesti keelega
    cities = [x.strip() for x in cities]


# see loeb dictionarysse võimalikud tuulesuunad (vastavalt kraadidele)
def readInWindDict():
    global wind_dict
    for i in range(361):
        if i == 0 or i == 360:
            wind_dict[i] = "põhjatuul"
        elif 0 < i < 90:
            wind_dict[i] = "kirdetuul"
        elif i == 90:
            wind_dict[i] = "idatuul"
        elif 90 < i < 180:
            wind_dict[i] = "kagutuul"
        elif i == 180:
            wind_dict[i] = "lõunatuul"
        elif 180 < i < 270:
            wind_dict[i] = "edelatuul"
        elif i == 270:
            wind_dict[i] = "läänetuul"
        elif 270 < i < 360:
            wind_dict[i] = "loodetuul"
        else:
            wind_dict[i] = "teadmata suunaga tuul"


# freim, mis jätab meelde endiselt küsitud küsimuse
weatherDict = {
     # küsitav linnanimi, nii näiteks kui see on olemas ja küsimuse "mis on temperatuur", mõistab bot,
     # mis linna temperatuuri küsitakse
    'city': None,
     # viimati küsitud parameetrid (listina selleks,et saaks korraga erinevaid asju küsida
    'last_parameters': [],
    # see vastab meile millisele päevale ilma öeldakse (täna, hetkel, praegu, nüüd, homme, ülehomme)
    'time': 'hetkel',
    # flag, mis vastab, kas oleme linna kohta vastuse juba andnud
    # (peaegu kasutu, aga vahepeal aitab õiget patternit leida)
    'answerGiven': False

}


# analüüsib meie teksti ja vastavalt suunab selle meetoditesse
def textAnalyzer(text):
    informationAsked = False  # flag, mis näitab, kas kasutaja on meilt midagi sisulist küsinud

    lemmasList = lemmalyzer(text)  # teeme saadud lause algvormi (listina)
    lemmaString = ""

    # seome algvormide listi tagasi terveks lauseks
    for index in range(len(lemmasList)):
        if index == len(lemmasList) - 1:
            # viimase sõna puhul ei taha tühikut lõppu!
            lemmaString += lemmasList[index]
        else:
            lemmaString += lemmasList[index] + " "

    # tervitavad sõnad, kui need esinevad, suure tõenäosusega tervitab meid kasutaja
    greetings = ["tere", "hei", "tsau", "hi", "privet", "Tere", "Hei", "Tsau", "Hi", "Privet"]

    # need sõnad on seotud ilmastikuga mingil hetkel, neile oskab ka süsteem vastata, saab aru vähemalt neist)
    weatherTriggers = ["temperatuur", "soe", "soojus", "niiskus", "õhuniiskus", "õhutemperatuur", "vihm", "sademed",
                       "sade", "ilm", "niisku", "õhurõhk", "rõhk", "niiske", "vihmane", "lumine", "päiksepaisteline",
                       "päikesepaisteline", "külma", "kraad",
                       "lumi", "päike", "tuul", "tuuline", "tuulesuund", "niiskustase", "niiskusprotsent", "tuulekiir",
                       "külm"]

    # ennustuste sõnad, need sõnad määravad, mis päevale tahame ennustust saada
    forecastTriggers = ["homme", "ülehomme", "hetkel", "praegu", "hetk", "nüüd", "täna"]

    # küsimuste sõnad - kus: tahame teada millegi asukohta, kell: tahame süsteemi kella, ülejäänud samuti asukoha omad
    questionWords = ["kus", "kell", "riik", "koordinaat", "koordinaadid"]

    vastus = ""  # mida tahame vastata

    # kasutaja tervitab meid, seega vastusesse paneme tervituse vastu
    if any(greeting in text for greeting in greetings):
        vastus += "Tere, "

    # kasutaja tutvustab end, eeldame, et ta ei otsusta ühes lauses tutvustada enda ja hakata küsima
    if len(re.findall('nimi\s+on\s+[A-Z][a-z]*|olen\s+[A-Z][a-z]*', text)) > 0:
        greetingAnalyzer(text)
        return "Tere, " + username + ", kuidas ma saan sind aidata?"

    city = None  # kas kasutajasisendist tuleb mingi linn välja
    time = None  # millise päeva kohta küsime
    weatherConditions = []  # kas kasutaja sisendis on midagi ilmaga seonduvat
    questionWordsAsked = []  # kas kasutaja sisendis on mingi muu küsimus
    #print("Lemmad: " + str(lemmasList))

    # sõnade järjestikune analüüsimine
    for lemma in lemmasList:
        # kas sõna on seotud ilmastikuga, kui jah, siis lisame ilmaga seodnduvate listi
        if lemma.lower() in weatherTriggers:
            weatherConditions.append(lemma)
            informationAsked = True
        # kas ennustuste sõna seotud, kui jah, kirjutame ülesse
        elif lemma.lower() in forecastTriggers:
            time = lemma.lower()
            informationAsked = True
        # kas tegemis on küsisõnaga
        elif lemma.lower() in questionWords:
            questionWordsAsked.append(lemma)
            informationAsked = True

    # leiame tekstist linnanime, kui selline on, toetatud on kuni
    # 2 sõnalised (võivad olla sidekriipsuga) suuretähelisd linnanimed
    if re.search('[A-Z][a-z]*([\s|-][A-Z][a-z]*)?', lemmaString) is not None:

        # potentsiaalse linna leidmine
        potentialCity = re.search('[A-ZÕÄÖÜ][a-zõäöü]*([\s|-][A-ZÕÄÖÜ][a-zõüöä]*)?', lemmaString)[0]
        # panen try, except sisse juhuks kui ikka seda importi pole

        # BOONUSPUNKT: Tõlgime linna inglise keelde Moskva -> Moscow
        translator = Translator()
        cityEnglish = translator.translate(potentialCity, dest='en')

        # kui selline inglisekeelne linn olemas, siis hea, leidsime linna
        if cityEnglish.text in cities:
            city = cityEnglish.text
            informationAsked = True
        else:
            # kui see ei aitanud, üritame muuta ascii'ks linnanime ja siis proovida, kas selline linna olemas
            cityEnglishAscii = utftoascii(cityEnglish.text)
            print(cityEnglishAscii)
            if cityEnglishAscii in cities:
                city = cityEnglishAscii
                informationAsked = True



    # kui meilt on midagi siulist küsitud, vastavame sellele, saadame olemasoleva info edasi
    if informationAsked:
        return vastus + weatherInputAnalyzer(city, weatherConditions, questionWordsAsked, time)
    # muul juhul on tegu kas lihtsalt tervitamisega või segase tekstiga, vastame vastavalt
    else:
        if len(vastus) > 0:
            return vastus + username
        return username + ", ma ei saa teist aru, palun proovige küsida teistmoodi! Ma oskan anda infot linna ilma " \
                          "kohta, asukoha kohta, teatada kellaaega!"


# antud meetod teeb lõviosa "reaalsest" tööst ära, tagastab kõik ilmastikuga ja asukohaga
# ja kellaga seotud vastused (peamiselt ikka ilm, seega selline nimi  õigustatud)
def weatherInputAnalyzer(city, weatherConditions, questionWordsAsked, time):
    global weatherDict

    # kontrollime järjest, kas saame enda mälufreimi midagi juurde panna
    if city is not None:
        weatherDict['city'] = city
    if time is not None:
        weatherDict['time'] = time
    if len(weatherConditions) > 0:
        weatherDict['last_parameters'] = weatherConditions

    # nüüd kontrollime, kas freimis on midagi puudu vajalikust informatsioonist (põhimõtteliselt piisab linnast
    # ja ilmastiku tingimusest)
    missingValues = []
    for key, value in weatherDict.items():
        if value == [] or value is None:
            missingValues.append(key)

    # kogu info olemas, saame vastata korrektselt
    if len(missingValues) == 0:

        # loeme sisse ilmastiku andmed
        data = weatherFunc(weatherDict)

        # hakkame vastust koostama alguses kujul "Linnas <linnanimi> on <ajamäärus> .... järgneb küsitud informatsioon
        vastus = "Linnas " + weatherDict['city'].title() + " on " + weatherDict['time'] + " "

        # meil kogu info freimis olemas, aga samas inimene küsis mingit sõna, mis seotud asukohaga,
        # tagastame talle informatsiooni antud linna asukoha kohta
        # NB! Tähtis, et seda me teeme, kui teame, et esialgsele ilmastiku küsimusele oleme vastanud (answergiven == True)
        if ("kus" in questionWordsAsked or "riik" in questionWordsAsked or "koordinaat" in questionWordsAsked
                    or "koordinaadid" in questionWordsAsked) and weatherDict['answerGiven']:
            vastus = username + ", linn " + weatherDict['city'] + " asub riigis: "

            # api tagastuste struktuur on weather ja forecast puhul, seega saame keyerrori kui ei erista riigi puhul forecasti
            # ja weatheri seega kui küsitakse kus, teeme ikkagi uue päringu!
            dataWhere = getDictFromJson('http://api.openweathermap.org/data/2.5/weather?q=' + weatherDict[
                'city'] + '&units=metric&APPID=' + APPID)

            vastus += getCountryByIso(
                dataWhere["sys"]["country"]) + ", linna koordinaadid on: " + str(
                dataWhere["coord"]["lon"]) + " kraadi pikkust ja " + str(dataWhere["coord"]["lat"]) + " kraadi laiust"

        # kui esineb märksõna "kell", anname kasutajale süsteemi kellaaja teada! Väike lisavõimalus
        elif "kell" in questionWordsAsked and weatherDict['answerGiven']:
            vastus = username + ", hetkel on kell: " + str(datetime.datetime.now().time()) + " ja kuupäev " + str(
                datetime.datetime.now().date())

        # Kui aga esineb sõna "ilm" ja eelnevad mitte, anname kogu informatsiooni ilma kotha:
        # temperatuur, üldine ilm, tuulekiirus, suund, niiskus, õhurõhk
        elif "ilm" in weatherDict['last_parameters']:
            weatherDict['answerGiven'] = True
            vastus += "temperatuur: " + str(int(data['main']['temp'])) + " kraadi, ilm on " + str(
                eng_est_dict[(data['weather'][0]['main'])]) + ", õhuniiskus on: " + str(
                int(data["main"]["humidity"])) + "%, õhurõhk: " + str(
                int(data["main"]["pressure"])) + " hpa, tuul puhub kiirusega " + str(
                int(data["wind"]["speed"])) + " m/s, puhub " + str(wind_dict[int(data['wind']['deg'])])
        else:
            # Muul juhul aga võis meil olla olukord kus kasutaja küsis ühte või mitut teist parameetrit
            for tingimus in weatherDict['last_parameters']:

                # Küsiti temperatuuri, lisame vastusele selle
                if tingimus == "soe" or tingimus == "temperatuur" or tingimus == "õhutemperatuur" or tingimus == "külm" or tingimus == "kraad" or tingimus == "külma":
                    vastus += " temperatuur: " + str(int(data['main']['temp'])) + " kraadi "

                # küsiti vihma/lume/päikese kohta, lisame selle vastusele
                elif tingimus == "vihmane" or tingimus == "päiksepaisteline" or tingimus == "päikesepaisteline" or tingimus == "pilvine" or tingimus == "lumine" or tingimus == "vihm" or tingimus == "lumi" or tingimus == "päike":
                    vastus += "ilm " + str(eng_est_dict[(data['weather'][0]['main'])]) + " "

                # küsiti õhuniiskuse kohta, lisame vastusele
                elif tingimus == "õhuniiskus" or tingimus == "niiskus" or tingimus == "niisku" or tingimus == "niiske" or tingimus == "niiskustase" or tingimus == "niiskusprotsent":
                    vastus += " õhuniiskus: " + str(int(data["main"]["humidity"])) + "% "

                # küsiti õhurõhu kohta, lisame vastusele
                elif tingimus == "rõhk" or tingimus == "õhurõhk":
                    vastus += " õhurõhk: " + str(int(data["main"]["pressure"])) + " hpa "

                # küsiti tuule kohta, lisame vastusele
                elif tingimus == "tuul" or tingimus == "tuuline" or tingimus == "tuulesuund" or tingimus == "tuulekiir":
                    vastus += " tuul kiirusega " + str(int(data['wind']['speed'])) + " m/s, puhub " + str(
                        wind_dict[int(data['wind']['deg'])])

                weatherDict['answerGiven'] = True  # nüüd vastus on antud!

        return vastus  # tagastame vastuse

    # andmeid jäi puudu või ei küsitud ilma kohta
    else:
        # küsiti jällegi asukoha kohta (aga freimis info ilma kohta puudu)
        if ("kus" in questionWordsAsked or "riik" in questionWordsAsked or "koordinaat" in questionWordsAsked or "koordinaadid" in questionWordsAsked) and weatherDict['city'] is not None:
            data = weatherFunc(weatherDict)
            return username + ", leidsin veidi infot sind huvitava linna " + weatherDict[
                'city'] + " asukoha kohta. Linn asub riigis: " + getCountryByIso(
                data["sys"]["country"]) + ", linna koordinaadid on: " + str(
                data["coord"]["lon"]) + " kraadi pikkust ja " + str(data["coord"]["lat"]) + " kraadi laiust"

        # küsiti kella
        elif "kell" in questionWordsAsked:
            return username + ", hetkel on kell: " + str(datetime.datetime.now().time()) + " ja kuupäev " + str(datetime.datetime.now().date())

        # Puudu on nii linn kui ka tingimused
        elif weatherDict['city'] is None and weatherDict['last_parameters'] == []:
            return username + ", palun täpsustage linnanime ja mida täpsemalt te teada tahate"

        # puudu on linnanimi
        elif weatherDict['city'] is None:
            return username + ", palun täpsustage linnanime, mille kohta infot soovite"

        # puudu on parameetrit linna kohta
        elif not weatherDict['last_parameters']:
            return username + ", palun täpsustage, mis asju te soovite linna " + weatherDict['city'].title() + " kohta teada!"


# tagastab api vastuse tänase, homse, ülehomse kohta
def weatherFunc(weatherDict):
    city = weatherDict['city']  # linn, mille kohta uurime
    if weatherDict['time'] == 'homme' or weatherDict['time'] == 'ülehomme':  # mis päevale on ilmastik
        date = datetime.datetime.now()  # saame arvuti kellaaja

        if weatherDict['time'] == 'homme':
            date += timedelta(hours=24)  # homsele ennustusele lisame 24 tundi juurde
        elif weatherDict['time'] == 'ülehomme':
            date += timedelta(hours=48)  # ülehomsele 48

        # loeme sisse ilma
        weather = getDictFromJson(
            'http://api.openweathermap.org/data/2.5/forecast?q=' + city + '&units=metric&APPID=' + APPID)

        #antud kellaaeg on api ennustuse vastuses lähim kellaaeg (ehk pm hetkemomendi jaoks lähim ennustus), sellega saamegi umbes 24/48 tundi hiljema ennustuse
        kell = str(weather['list'][0]['dt_txt'].split(" ")[1])

        for i in range(len(weather['list'])):  # leiame just selle ilma, milline päev meil hetkel on!
            if str(date.date()) in weather['list'][i]['dt_txt'] and kell in weather['list'][i]['dt_txt']:
                weather = weather['list'][i]
                break  # kui leitud, lõpetame otsingu

        return weather

    # hetke ilm
    return getDictFromJson('http://api.openweathermap.org/data/2.5/weather?q=' + city + '&units=metric&APPID=' + APPID)


# teksti lemmadelistiks muutmine
def lemmalyzer(stripped_text):
    words = stripped_text.split(" ")
    lemmas = []
    for word in words:
        # "-" kaotab lemmatiseerija ära, seda me ei tahaks. jagame kaheks linnanime ja laseme
        # iga osa lemmatiseerijast läbi
        if "-" in word:
            wordsList = word.split("-")
            s6na1 = urllib.request.urlopen(
                'http://prog.keeleressursid.ee/ws_etmrf/lemma.php?s=' + urllib.parse.quote(wordsList[0]))
            analyys1 = json.loads(s6na1.read().decode())
            s6na2 = urllib.request.urlopen(
                'http://prog.keeleressursid.ee/ws_etmrf/lemma.php?s=' + urllib.parse.quote(wordsList[1]))
            analyys2 = json.loads(s6na2.read().decode())
            if analyys1['root'] and analyys2['root']:
                lemmas.append(analyys1['root'].strip("") + "-" + analyys2['root'].strip(""))
        else:
            file = urllib.request.urlopen(
                'http://prog.keeleressursid.ee/ws_etmrf/lemma.php?s=' + urllib.parse.quote(word))
            analyys = json.loads(file.read().decode())
            if analyys['root']:
                lemmas.append(analyys['root'].strip(""))
    return lemmas


# kasutaja nime salvestamine
def greetingAnalyzer(text):
    global username
    nameStatements = re.findall('nimi\s+on\s+[A-Z][a-z]*|olen\s+[A-Z][a-z]*', text)
    if len(nameStatements) > 0:
        nameStatement = nameStatements[-1]
        pieces = nameStatement.split(" ")
        username = pieces[-1]


# teeb sõnest ascii (leitud kuskil internetis)
def utftoascii(potentialcity):
    asciiform = unicodedata.normalize('NFKD', potentialcity)
    return u"".join([c for c in asciiform if not unicodedata.combining(c)])


# veebilehelt info lugemine
def getDictFromJson(url):
    # Veebist ilmainfo lugemine, kodutööna esitatavas versioonis peab olema just järgmised kaks rida kasutuses!!!
    file = urllib.request.urlopen(url)
    data = json.loads(file.read().decode())
    return data


# riigi saamine iso koodi põhjal
def getCountryByIso(iso):
    country = ""
    file = urllib.request.urlopen("http://prog.keeleressursid.ee/ws_riigid/index.php?iso=" + iso)
    # Päring: http://prog.keeleressursid.ee/ws_riigid/index.php?iso=<ISO kood>
    # ISO kahetähelised koodid: https://en.wikipedia.org/wiki/ISO_3166-1
    # Vastus: riigi nimi (eesti keeles)
    country += file.read().decode()
    return country


# Registreerige ennast http://openweathermap.org/ kasutajaks (ei pea kasutama oma kõige olulisemat e-posti aadressi)
# API Key leiate https://home.openweathermap.org/api_keys, kopeerige see sõnena APPID muutuja väärtuseks
APPID = '48620b1611c47adce31f2aaeb7e2b95d'
