import asyncio, json, gspread, datetime, ast, sys, tweepy, time, threader
# from twilio.rest import Client
from pyppeteer import launch

class Julkaisija:
    def __init__(self, numero: int):
        self.numero = numero
        self.numero_str = str(numero)

    async def init(self, page: "Page", peleja: int):
        # print(f"Haetaan pelaajan nimi, peleja on {peleja}")
        self.nimi = (await paikka_tekstiksi(f"div.col-xl-6:nth-child({self.numero_str}) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > a:nth-child(1)", page)).strip()
        self.kokonaispisteet = int(await paikka_tekstiksi(f"div.col-xl-6:nth-child({self.numero_str}) > div:nth-child(2) > table:nth-child(2) > tbody:nth-child(2) > tr:nth-child({str(peleja + 2)}) > td:nth-child(2)", page))
        self.pelit = []
        for i in range(1, peleja + 1):
            pelin_nimi, kriitikot, pisteet = await self.pelin_tiedot(self.numero, i, page)
            if pelin_nimi == None:
                break
            # print(f"Lisätään pelaajan pelilistaan {pelin_nimi}, {kriitikot}, {pisteet}")
            self.pelit.append([pelin_nimi, kriitikot, pisteet])

        self.counterpick = await self.pelin_tiedot(self.numero, peleja + 1, page)

    def __str__(self):
        return f"Julkaisija({self.numero}, {self.nimi}, {self.kokonaispisteet}, {self.pelit}"

    def __repr__(self):
        return self.__str__()


    async def pelin_tiedot(self, pelaaja: int, peli: int, page: "Page") -> tuple:
        pelaaja_str = str(pelaaja)
        peli_str = str(peli)
        try:
            paikka = f"div.col-xl-6:nth-child({pelaaja_str}) > div:nth-child(2) > table:nth-child(2) > tbody:nth-child(2) > tr:nth-child({peli_str}) > td:nth-child(1) > span:nth-child(1) > div:nth-child(1) > div:nth-child(1) > span:nth-child(1) > span:nth-child(2)"
            pelin_nimi = await paikka_tekstiksi(paikka, page)
            pelin_nimi = pelin_nimi.strip()
        except:
            return (None, None, None)
        if pelin_nimi == "":
            return (None, None, None)

        # print("Tsekataan kriitikoiden ja pisteiden paikka")
        kriitikot_paikka, pisteet_paikka = [f"div.col-xl-6:nth-child({pelaaja_str}) > div:nth-child(2) > table:nth-child(2) > tbody:nth-child(2) > tr:nth-child({peli_str}) > td:nth-child({sarake})" for sarake in range(2, 4)]
        # print("Haetaan kriitikoiden pisteet")
        kriitikot = await paikka_tekstiksi(kriitikot_paikka, page)
        # print(f"Jotka ovat {kriitikot}")
        # print("Haetaan fantasy-pisteet")
        pisteet = await paikka_tekstiksi(pisteet_paikka, page)
        # print(f"Jotka ovat {pisteet}")
        kriitikot = int(kriitikot) if kriitikot != "--" and kriitikot != None else 0
        pisteet = int(pisteet) if pisteet != "--" and pisteet != None else 0
        return (pelin_nimi, kriitikot, pisteet)

async def paikka_tekstiksi(paikka: str, page: "Page") -> str:
    elem = await page.querySelector(paikka)
    if elem == None:
        return None
    else:
        evaluoitu = await page.evaluate('(element) => element.textContent', elem)
        # print(f"evaluoitu on {evaluoitu}")
        return evaluoitu

def tallenna_pelaajat(tiedostonnimi: str, pelaajat: list):
    time.sleep(2)
    with open(tiedostonnimi, "w") as f:
        for p in pelaajat:
            dump = json.dumps(p.__dict__, ensure_ascii=False)
            f.write(dump)
            f.write("\n")

def lataa_pelaajat(tiedostonnimi: str) -> list:
    ladatut = []
    with open(tiedostonnimi) as f:
        for rivi in f:
            lisattava = eval(rivi)
            ladatut.append(lisattava)
    palautettavat = []
    for pelaaja in ladatut:
        lisattava = Julkaisija(pelaaja["numero"])
        lisattava.nimi = pelaaja["nimi"]
        lisattava.pelit = pelaaja["pelit"]
        lisattava.kokonaispisteet = pelaaja["kokonaispisteet"]
        lisattava.counterpick = pelaaja["counterpick"]
        palautettavat.append(lisattava)

    return palautettavat

def tallenna_sheetsiin_olioista(sheet: str, pelaajat: list, peleja: int):
    print("oauthataan")
    gc = gspread.service_account()
    sh = gc.open_by_key(sheet)
    paiva = datetime.datetime.now().strftime("%d.%m.%Y")
    vuosi = datetime.datetime.now().strftime("%Y")

    print("avataan vuoden worksheetti")
    try:
        ws = sh.worksheet(vuosi)
    except:
        ws = sh.add_worksheet(title=vuosi, rows=str(peleja + 5), cols=str(len(pelaajat) * 4))
    
    pelit = []
    print("Käsitellään pelit")
    
    # for pelaaja in pelaajat:
    #     for i in range(len(pelaaja.pelit)):
    #         rivi = []
    #         rivi.extend(pelaaja.pelit[i])
    #         rivi.append("")
    #     pelit.append(rivi)
    # print("Pelit:\n{pelit}")
    # time.sleep(2)
    
    suurin_pelimaara = len(max(pelaajat, key= lambda p: len(p.pelit)).pelit)
    print(f"Suurin pelimäärä on {suurin_pelimaara}")
    
    for i in range(suurin_pelimaara):
        rivi = []
        for j in range(len(pelaajat)):
            if i < len(pelaajat[j].pelit):
                rivi.extend(pelaajat[j].pelit[i])
            else:
                rivi.extend(["", "", ""])
            rivi.append("")
        pelit.append(rivi)


    nimirivi = []
    for i in range(len(pelaajat)):
        nimirivi.append([pelaajat[i].nimi])   
        nimirivi.extend([[], [pelaajat[i].kokonaispisteet], []])

    counterpickit = []
    for i in range(len(pelaajat)):
        counterpickit.extend([[f"counter-pick: {pelaajat[i].counterpick[0]}"], [pelaajat[i].counterpick[1]], [pelaajat[i].counterpick[2]], []])   

    print("Päivitetään worksheettiä")
    ws.update("A1:1", nimirivi, major_dimension="COLUMNS")
    ws.update("A3:AZ1000", pelit, major_dimension="ROWS")
    ws.update(f"A{peleja + 4}:{peleja + 4}", counterpickit, major_dimension="COLUMNS")
    
    
    try:
        ws_kertyma = sh.worksheet(f"{vuosi}_kertyma")
    except:
        ws_kertyma = sh.add_worksheet(title=f"{vuosi}_kertyma", rows="380", cols=str(len(pelaajat) + 2))

    kertyman_nimirivi = [["Päivämäärä"]]
    for i in range(len(pelaajat)):
        kertyman_nimirivi.append([pelaajat[i].nimi])
    

    ws_kertyma.update("A1:1", kertyman_nimirivi, major_dimension="COLUMNS")
    sarakkeet_list = list(filter(None, ws_kertyma.col_values(1)))
    eka_tyhja_rivi = str(len(sarakkeet_list)+1)
    paivan_pisteet = [[paiva]]
    for i in range(len(pelaajat)):
        paivan_pisteet.append([pelaajat[i].kokonaispisteet])
    ws_kertyma.update(f"A{eka_tyhja_rivi}:{eka_tyhja_rivi}", paivan_pisteet, major_dimension="COLUMNS")


def vertaa_pelaajalistoja(vanhojen_lista: list, uusien_lista: list) -> str:
    palaute = []
    if len(vanhojen_lista) != len(uusien_lista):
        print("Vertailtavat listat eripituiset")
        return ["Virhe"]
    
    vanha_tilanne = sorted([(kisailija.nimi, kisailija.kokonaispisteet) for kisailija in vanhojen_lista], key=lambda p: p[1], reverse=True)
    uusi_tilanne = sorted([(kisailija.nimi, kisailija.kokonaispisteet) for kisailija in uusien_lista], key=lambda p: p[1], reverse=True)
    if vanha_tilanne != uusi_tilanne:
        vanha_ranking = ""
        uusi_ranking = ""
        for p in vanha_tilanne:
            vanha_ranking += f"{p[0]} {p[1]} pistettä,\n"
        for p in uusi_tilanne:
            uusi_ranking += f"{p[0]} {p[1]} pistettä,\n"
        kerrottava = f"Pistetilanne päivittynyt!\n\nUusi tilanne:\n{uusi_ranking}\nVanha tilanne:\n{vanha_ranking}"
        palaute.append(kerrottava)
    
    # TODO - korjaa tätä
    for i in range(len(vanhojen_lista)):
        kerrottava = ""
        if len(vanhojen_lista[i].pelit) != len(uusien_lista[i].pelit):
            kerrottava += f"Pelaajalla {vanhojen_lista[i].nimi} on uusia pelejä!:\n"
            for peli in uusien_lista[i].pelit[len(vanhojen_lista[i].pelit):]:
                kerrottava += f"{peli[0]}\n"
        if kerrottava != "":
            palaute.append(kerrottava)
    
    return palaute

def twiittaa(teksti: str, api: 'tweepy.api.API'):
    thread = threader.Thread(api)
    username = 'UnelmienP'
    thread.post_thread(teksti, username)
    
    # if len(teksti) <= 280:
    #     api.update_status(teksti)
    # else:
    #     pilkottu = teksti.split("\n")
    #     postattavat = []
    #     while sum([len(patka) + len(pilkottu) - 1 for patka in pilkottu]) > 280:
    #         yksittainen_twiitti = ""
    #         while True:
    #             yksittainen_twiitti += pilkottu[0] + "\n"
    #             pilkottu.pop(0)
    #             if len(pilkottu) == 0 or len(yksittainen_twiitti) + len(pilkottu[0]) > 279:
    #                 break
    #         postattavat.append(yksittainen_twiitti)
    #     postattavat.append("\n".join(pilkottu))
        
    #     edellinen_postattu = api.update_status(postattavat[0]).id
    #     for postattava in postattavat[1:]:
    #         edellinen_postattu = api.update_status(status=postattava, 
    #         in_reply_to_status_id=edellinen_postattu.id, auto_populate_reply_metadata=True)
        
        # tai sitten näin
        # for postattava in postattavat:
        #     api.update_status(postattava)
        

# def postaa_whatsappiin(viesti: str):
#     with open("twilio.txt") as f:
#         twiliot = json.loads(f.read())
#     client = Client(twiliot["sid"], twiliot["token"])

#     message = client.messages.create(body = viesti,
#                                     from_='whatsapp:+14155238886',
#                                     to='whatsapp:+3581231231231')

async def main():
    
    with open(sys.argv[1]) as f:
        asetukset = json.loads(f.read())
    
    print(f"Käsitellään liiga {asetukset['nimi']}")
    browser = await launch(executablePath='/usr/bin/chromium')
    page = await browser.newPage()
    
    await page.goto(asetukset["liiga"])
    
    pelaajat = []
    for pelaajan_nro in range(1, asetukset["pelaajia"] + 1):
        # print(f"Käsitellään pelaaja {pelaajan_nro}")
        pelaajat.append(Julkaisija(pelaajan_nro))
        await pelaajat[pelaajan_nro - 1].init(page, asetukset["peleja"])

    await browser.close()
    
    print("Käynnistetään tallenna sheetsiin olioista")
    tallenna_sheetsiin_olioista(asetukset["sheet"], pelaajat, asetukset["peleja"])
    

    # Tämä allaoleva kokonaisuus ei ole uuden vuoden aloittamista ajatellen ihan
    # suoraviivaisesti muokattavissa
    print("ladataan vanhat")
    ladatut = lataa_pelaajat(asetukset["tekstitiedosto"])
    
    # Poiskommentoi tämä uutta liigaa aloittaessa, jotta saatinitialisoitua tulostiedoston
    print("Tallennetaan uudet")
    tallenna_pelaajat(asetukset["tekstitiedosto"], pelaajat)
    
    print("Vertaillaan")
    vertailun_palaute = vertaa_pelaajalistoja(ladatut, pelaajat)

    if vertailun_palaute != []:
        print(f"Muutoksia tilanteessa: {vertailun_palaute}")
        
        # postailut someen
        with open("twitter_keys.txt") as f:
            avaimet = ast.literal_eval(f.read())
        auth = tweepy.OAuthHandler(avaimet["API_key"], avaimet["API_secret"])
        auth.set_access_token(avaimet["access_token"], avaimet["access_secret"])
        api = tweepy.API(auth, wait_on_rate_limit=True,
            wait_on_rate_limit_notify=True)
        for i in vertailun_palaute:
            twiittaa(f"{asetukset['nimi']}:\n{i}", api)
        

        # tänne viikottaiset spämmikoosteet:
        if datetime.datetime.today().weekday() == 6:
            ladatut_vko = lataa_pelaajat("vko_" + asetukset["tekstitiedosto"])
            vertailun_palaute_vko = vertaa_pelaajalistoja(ladatut_vko, pelaajat)
            if vertailun_palaute_vko != []:
                # print(f"Whatsappiin lähtee {str(pelaajat)}")
                # postaa_whatsappiin(str(pelaajat))
                # tms viikkospämmi
                pass
            tallenna_pelaajat("vko_" + asetukset["tekstitiedosto"], pelaajat)
            pass
        
    tallenna_pelaajat(asetukset["tekstitiedosto"], pelaajat)

asyncio.get_event_loop().run_until_complete(main())