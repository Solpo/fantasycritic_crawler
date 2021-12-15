import asyncio
from pyppeteer import launch

async def paikka_tekstiksi(paikka: str, page: "Page") -> str:
    try:
        elem = await page.querySelector(paikka)
        return await page.evaluate('(element) => element.textContent', elem)
    except:
        print("Joku virhe\n")
        return "Virhe"

async def main():
    browser = await launch(executablePath='/usr/bin/chromium')
    page = await browser.newPage()
    # kissoja ja pelailua
    await page.goto('https://www.fantasycritic.games/league/75a11364-2afc-4ef8-ba4c-318a4fa4bfba/2021')
    
    
    while True:
        syote = input("Anna CSS-osoite: ")
        if syote == "q":
            break
        elementin_teksti = await paikka_tekstiksi(syote, page)
        print(f"Siinä lukee: \n{elementin_teksti}")
        

    await browser.close()
asyncio.get_event_loop().run_until_complete(main())

# div.table-responsive:nth-child(2) > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(3)
# div.table-responsive:nth-child(2) > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(5) > span:nth-child(1) 

#__BVID__97 > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(3) > 

# div.table-responsive:nth-child(2) > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(3)