import httpx
import asyncio
from bs4 import BeautifulSoup
import re
import lxml
from pprint import pprint
import os
import pickle
import datetime
import aiofiles
from config.settings import use_cache, file_ttl_minutes


file_ttl = datetime.timedelta(minutes=file_ttl_minutes)


async def get_stocks_info():
    resp = await get_cached_info('get_stocks_info')
    if resp:
        return resp

    url  = 'https://statusinvest.com.br/category/advancedsearchresult?search=%7B%22Sector%22%3A%22%22%2C%22SubSector%22%3A%22%22%2C%22Segment%22%3A%22%22%2C%22my_range%22%3A%220%3B25%22%2C%22dy%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22p_L%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22p_VP%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22p_Ativo%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22margemBruta%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22margemEbit%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22margemLiquida%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22p_Ebit%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22eV_Ebit%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22dividaLiquidaEbit%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22dividaliquidaPatrimonioLiquido%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22p_SR%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22p_CapitalGiro%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22p_AtivoCirculante%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22roe%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22roic%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22roa%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22liquidezCorrente%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22pl_Ativo%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22passivo_Ativo%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22giroAtivos%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22receitas_Cagr5%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22lucros_Cagr5%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%2C%22liquidezMediaDiaria%22%3A%7B%22Item1%22%3Anull%2C%22Item2%22%3Anull%7D%7D&CategoryType=1'
    headers = {
      'accept': '*/*',
      'accept-language': 'en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7,es-MX;q=0.6,es;q=0.5',
      'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
      'x-requested-with': 'XMLHttpRequest',
      'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="97", "Chromium";v="97"',
      'sec-ch-ua-mobile': '?0',
      'sec-ch-ua-platform': '"macOS"',
      'sec-fetch-dest': 'empty',
      'sec-fetch-mode': 'cors',
      'sec-fetch-site': 'same-origin',
      'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)'
    }
    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.get(url, headers=headers)

    await save_cached_info('get_stocks_info', resp)
    return resp


async def get_stocks_historical_info(ticker: str):
    resp = await get_cached_info(f'get_stocks_historical_info_{ticker}')
    if resp:
        return ticker, resp

    url = 'https://statusinvest.com.br/acao/indicatorhistorical'
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7,es-MX;q=0.6,es;q=0.5',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'x-requested-with': 'XMLHttpRequest',
        'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="97", "Chromium";v="97"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)'
    }
    args = f'ticker={ticker}&time=5'
    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.post(f"{url}?{args}", headers=headers)
    await save_cached_info(f'get_stocks_historical_info_{ticker}', resp)
    return ticker, resp


async def get_stocks_historical_price(ticker: str):
    resp = await get_cached_info(f'get_stocks_historical_price_{ticker}')
    if resp:
        return ticker, resp

    url = 'https://statusinvest.com.br/acao/tickerprice'
    headers = {
      'accept': '*/*',
      'accept-language': 'en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7,es-MX;q=0.6,es;q=0.5',
      'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
      'x-requested-with': 'XMLHttpRequest',
      'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)'
    }
    args = f'ticker={ticker}&type=4&currences%5B%5D=1'
    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.post(f"{url}?{args}", headers=headers)

    await save_cached_info(f'get_stocks_historical_price_{ticker}', resp)
    return ticker, resp


async def get_stocks_page_info(ticker):
    resp = await get_cached_info(f'get_stocks_page_info_{ticker}')
    if resp:
        return ticker, resp
    url = f'https://statusinvest.com.br/acoes/{ticker}'
    headers = {
      'accept': '*/*',
      'accept-language': 'en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7,es-MX;q=0.6,es;q=0.5',
      'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
      'x-requested-with': 'XMLHttpRequest',
      'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)'
    }
    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.get(url, headers=headers)

    await save_cached_info(f'get_stocks_page_info_{ticker}', resp)
    return ticker, resp


async def save_cached_info(identifier, obj):
    if not use_cache:
        return

    if not os.path.exists('cache'):
        os.makedirs('cache')

    async with aiofiles.open(f"cache/{identifier}.cache", 'wb') as f:
        pickled_foo = pickle.dumps(obj)
        await f.write(pickled_foo)


async def get_cached_info(identifier: str):
    if not use_cache:
        return None

    if not os.path.exists('cache'):
        os.makedirs('cache')

    file_name = f"cache/{identifier}.cache"
    if not os.path.exists(file_name):
        return None

    if (datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getctime(file_name))).min > file_ttl:
        os.remove(file_name)
        return None

    async with aiofiles.open(file_name, 'rb') as f:
        pickled_foo  = await f.read()

    return pickle.loads(pickled_foo)


async def format_stock_page(page_content: bytes):
    regex = re.compile("^[-\d\,%\.]*$")
    page = BeautifulSoup(page_content, "html.parser") 
    dom = lxml.etree.HTML(str(page)) 
    elements = dom.xpath('//div[@id="company-section"]//div[@class="info"]')
    result = {}
    tag = ''
    for element in elements:
        children = element.xpath('./div//div//strong|./div//div//h3|./div//div//span[@class="d-inline-block mr-2"]')
        for child in children:
            if child.text and not child.attrib['class'] == 'title m-0 legend-tooltip':
                if child.tag in {'h3', 'span'}:
                    tag = child.text
                else:
                    result[tag] = child.text
                    if child.text == '--%':
                        result[tag] = '0%'

                    if regex.match(result[tag]):
                        result[tag] = float(result[tag].replace('.', '').replace('%', '').replace(',', '.'))

    elements_sector = dom.xpath('//div[@id="company-section"]//div[@class="top-info top-info-1 top-info-sm-2 top-info-md-n sm d-flex justify-between"]//div[contains(@class, "info")]')
    for element in elements_sector:
        children = element.xpath('./div//div//strong|./div//div//span')
        for child in children:
            if child.text and not child.attrib['class'] == 'title m-0 legend-tooltip':
                if child.tag in {'h3', 'span'}:
                    tag = child.text
                else:
                    result[tag] = child.text
    return result


async def main():
    resp = await get_stocks_info()
    # for item in resp.json():
        # results = await asyncio.gather(
            # get_stocks_historical_info(item.get('ticker')),
            # get_stocks_historical_price(item.get('ticker')),
            # get_stocks_page_info(item.get('ticker'))
        # )
        # break
    for ticker in resp.json():
        if ticker.get('ticker') == 'VALE3':
            pprint(ticker)
            break
    hist = await get_stocks_historical_info('VALE3')
    pprint(hist[1].json())
    page = await get_stocks_page_info('VALE3')
    results = format_stock_page(page[1].content)
    pprint(results)


if __name__ == '__main__':
    asyncio.run(main())
