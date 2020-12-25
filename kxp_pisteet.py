import asyncio, json, gspread
from pyppeteer import launch

async def paikka_tekstiksi(paikka: str, page: "Page") -> str:
    elem = await page.querySelector(paikka)
    return await page.evaluate('(element) => element.textContent', elem)

class Julkaisija:
    def __init__(self, numero: int):
        self.numero = numero
        self.numero_str = str(numero)

    async def init(self, page: "Page"):
        self.nimi = (await paikka_tekstiksi(f"div.col-xl-6:nth-child({self.numero_str}) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > a:nth-child(1)", page)).strip()
        self.kokonaispisteet = int(await paikka_tekstiksi(f"div.col-xl-6:nth-child({self.numero_str}) > div:nth-child(1) > table:nth-child(2) > tbody:nth-child(2) > tr:nth-child(16) > td:nth-child(2)", page))

        # Määrittele manuaalisesti, kuinka monta paikkaa vuoden listalla on
        self.pelit = []
        peleja = 14
        for i in range(1, peleja + 1):
            pelin_nimi, kriitikot, pisteet = await self.pelin_tiedot(self.numero, i, page)
            if pelin_nimi == "":
                break
            self.pelit.append((pelin_nimi, kriitikot, pisteet))

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
            print(f"tallennetaan tiedostoon pelaajalle x dumppi")
            f.write(dump)
            f.write("\n")

def lataa_pelaajat(tiedostonnimi: str) -> list:
    palautettavat = []
    with open(tiedostonnimi) as f:
        for rivi in f:
            lisattava = eval(rivi)
            palautettavat.append(lisattava)
    return palautettavat

def tallenna_sheetsiin_dictista(pelaajat: list):
    gc = gspread.oauth()
    sh = gc.open_by_key("1GnBiI_bkm2dT5CY4XmPbN7rIQDRotL96P_3i-cAOF2c")
    ws = sh.worksheet("Sheet1")
    pelit = []
    
    for i in range(len(pelaajat[0]["pelit"])):
        rivi = []
        for j in range(len(pelaajat)):
            rivi.extend([pelaajat[j]["pelit"][i][0]])
            rivi.extend([pelaajat[j]["pelit"][i][1]])
            rivi.extend([pelaajat[j]["pelit"][i][2]])
            rivi.append("")
        pelit.append(rivi)
        # pelit.append([pelaajat[j][pelit][i][0], pelaajat[j][pelit][i][1], pelaajat[j][pelit][i][2] for j in range(1, 4)])

    ws.update("A3:AZ1000", pelit, major_dimension="ROWS")
    
def tallenna_sheetsiin_olioista(pelaajat: list):
    gc = gspread.oauth()
    sh = gc.open_by_key("1GnBiI_bkm2dT5CY4XmPbN7rIQDRotL96P_3i-cAOF2c")
    ws = sh.worksheet("Sheet1")
    pelit = []
    
    for i in range(len(pelaajat[0].pelit)):
        rivi = []
        for j in range(len(pelaajat)):
            rivi.extend([pelaajat[j].pelit[i][0]])
            rivi.extend([pelaajat[j].pelit[i][1]])
            rivi.extend([pelaajat[j].pelit[i][2]])
            rivi.append("")
        pelit.append(rivi)
        # pelit.append([pelaajat[j][pelit][i][0], pelaajat[j][pelit][i][1], pelaajat[j][pelit][i][2] for j in range(1, 4)])

    ws.update("A3:AZ1000", pelit, major_dimension="ROWS")

async def main():
    browser = await launch(executablePath='/usr/bin/chromium')
    page = await browser.newPage()
    await page.goto('https://www.fantasycritic.games/league/fb4b4799-2b50-45d1-803b-658a7dddf3f6/2020')
    # await page.goto('https://www.fantasycritic.games/league/640b5986-eff6-4690-8701-14270ae5e18c/2021')

    # Määrittele manuaalisesti, paljonko pelaajia on
    pelaajia = 3
    pelaajat = []
    for pelaajan_nro in range(1, pelaajia + 1):
        pelaajat.append(Julkaisija(pelaajan_nro))
        await pelaajat[pelaajan_nro - 1].init(page)

    tallenna_sheetsiin_olioista(pelaajat)

    # tallenna_pelaajat("test2.txt", pelaajat)

    # print("ladataan pelaajat")
    # ladatut = lataa_pelaajat("test2.txt")

    

    await browser.close()



asyncio.get_event_loop().run_until_complete(main())


# async def hae_pelaaja(numero: int) -> dict:
#     numero_str = str(numero)
#     pelaaja_dict= {}
#     nimi_elem = await page.querySelector(f"div.col-xl-6:nth-child({numero_str}) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > a:nth-child(1)")
#     kokonaispisteet_elem = await page.querySelector(f"div.col-xl-6:nth-child({numero_str}) > div:nth-child(1) > table:nth-child(2) > tbody:nth-child(2) > tr:nth-child(16) > td:nth-child(2)")
#     kriitikot = await page.evaluate('(element) => element.textContent', kriitikot_elem)
