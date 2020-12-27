import asyncio, json, gspread, datetime, ast, sys
# from twilio.rest import Client
from pyppeteer import launch

async def paikka_tekstiksi(paikka: str, page: "Page") -> str:
    elem = await page.querySelector(paikka)
    return await page.evaluate('(element) => element.textContent', elem)

class Julkaisija:
    def __init__(self, numero: int):
        self.numero = numero
        self.numero_str = str(numero)

    async def init(self, page: "Page", peleja: int):
        self.nimi = (await paikka_tekstiksi(f"div.col-xl-6:nth-child({self.numero_str}) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > a:nth-child(1)", page)).strip()
        self.kokonaispisteet = int(await paikka_tekstiksi(f"div.col-xl-6:nth-child({self.numero_str}) > div:nth-child(1) > table:nth-child(2) > tbody:nth-child(2) > tr:nth-child({str(peleja + 2)}) > td:nth-child(2)", page))

        self.pelit = []
        for i in range(1, peleja + 1):
            pelin_nimi, kriitikot, pisteet = await self.pelin_tiedot(self.numero, i, page)
            if pelin_nimi == "":
                break
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
            paikka = f"div.col-xl-6:nth-child({pelaaja_str}) > div:nth-child(1) > table:nth-child(2) > tbody:nth-child(2) > tr:nth-child({peli_str}) > td:nth-child(1) > span:nth-child(1) > div:nth-child(1) > div:nth-child(1) > span:nth-child(1) > span:nth-child(2)"
            pelin_nimi = await paikka_tekstiksi(paikka, page)
            pelin_nimi = pelin_nimi.strip()
        except:
            print("Ei peliä tässä kohtaa")
            return (None, None, None)
        if pelin_nimi == "":
            return (None, None, None)

        kriitikot_paikka, pisteet_paikka = [f"div.col-xl-6:nth-child({pelaaja_str}) > div:nth-child(1) > table:nth-child(2) > tbody:nth-child(2) > tr:nth-child({peli_str}) > td:nth-child({sarake})" for sarake in range(2, 4)]
        kriitikot = await paikka_tekstiksi(kriitikot_paikka, page)
        pisteet = await paikka_tekstiksi(pisteet_paikka, page)
        kriitikot = int(kriitikot) if kriitikot != "--" else 0
        pisteet = int(pisteet) if pisteet != "--" else 0
        return (pelin_nimi, kriitikot, pisteet)

def tallenna_pelaajat(tiedostonnimi: str, pelaajat: list):
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
    gc = gspread.oauth()
    sh = gc.open_by_key(sheet)
    paiva = datetime.datetime.now().strftime("%d.%m.%Y")
    vuosi = datetime.datetime.now().strftime("%Y")

    try:
        ws = sh.worksheet(vuosi)
    except:
        ws = sh.add_worksheet(title=vuosi, rows=str(peleja + 5), cols=str(len(pelaajat) * 4))
    
    pelit = []

    for i in range(len(pelaajat[0].pelit)):
        rivi = []
        for j in range(len(pelaajat)):
            rivi.extend(pelaajat[j].pelit[i])
            rivi.append("")
        pelit.append(rivi)

    nimirivi = []
    for i in range(len(pelaajat)):
        nimirivi.append([pelaajat[i].nimi])   
        nimirivi.extend([[], [pelaajat[i].kokonaispisteet], []])

    counterpickit = []
    for i in range(len(pelaajat)):
        counterpickit.extend([[f"counter-pick: {pelaajat[i].counterpick[0]}"], [pelaajat[i].counterpick[1]], [pelaajat[i].counterpick[2]], []])   

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
            vanha_ranking += f"{p[0]}, {p[1]} pistettä\n"
        for p in uusi_tilanne:
            uusi_ranking += f"{p[0]}, {p[1]} pistettä\n"
        kerrottava = f"Pistetilanne päivittynyt!\nVanha tilanne:\n{vanha_ranking}\nUusi tilanne:\n{uusi_ranking}"
        palaute.append(kerrottava)
    
    for i in range(len(vanhojen_lista)):
        kerrottava = ""
        if len(vanhojen_lista[i].pelit) != len(uusien_lista[i].pelit):
            kerrottava += f"Pelaajalla {vanhojen_lista[i].nimi} on uusia pelejä!:\n"
            for peli in uusien_lista[i].pelit[len(vanhojen_lista[i].pelit):]:
                kerrottava += f"{peli[0]}\n"
        if kerrottava != "":
            palaute.append(kerrottava)
    
    return palaute

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
    
    print(f"Käsitellään liiga {sys.argv[1]}")
    browser = await launch(executablePath='/usr/bin/chromium')
    page = await browser.newPage()
    
    await page.goto(asetukset["liiga"])
    
    pelaajat = []
    for pelaajan_nro in range(1, asetukset["pelaajia"] + 1):
        pelaajat.append(Julkaisija(pelaajan_nro))
        await pelaajat[pelaajan_nro - 1].init(page, asetukset["peleja"])

    tallenna_sheetsiin_olioista(asetukset["sheet"], pelaajat, asetukset["peleja"])
    
    
    # # Poiskommentoi tämä uutta liigaa aloittaessa, jotta saatinitialisoitua tulostiedoston
    # tallenna_pelaajat(asetukset["tekstitiedosto"], pelaajat)

    # tulospostaukset sunnuntaisin
    if datetime.datetime.today().weekday() == 6:
        ladatut = lataa_pelaajat(asetukset["tekstitiedosto"])

        vertailun_palaute = vertaa_pelaajalistoja(ladatut, pelaajat)
        print(vertailun_palaute)
        if vertailun_palaute != []:
            # some tänne
            # print(f"Whatsappiin lähtee {str(pelaajat)}")
            # postaa_whatsappiin(str(pelaajat))
            pass

        tallenna_pelaajat(asetukset["tekstitiedosto"], pelaajat)
    await browser.close()

asyncio.get_event_loop().run_until_complete(main())