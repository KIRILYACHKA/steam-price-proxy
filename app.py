from flask import Flask, request, jsonify
import requests
import os
import re
import time
from functools import lru_cache
from bs4 import BeautifulSoup

app = Flask(__name__)

# Просте кешування: ключ = item name, значення = (timestamp, data)
CACHE_TTL = 300  # 5 хвилин
cache = {}

def get_cached(item):
    rec = cache.get(item)
    if rec and time.time() - rec[0] < CACHE_TTL:
        return rec[1]
    return None

def set_cache(item, data):
    cache[item] = (time.time(), data)

@app.route('/steam-price')
def get_price():
    item = request.args.get('item')
    if not item:
        return jsonify({'error': 'Item name is required'}), 400

    # перевір кеш
    cached = get_cached(item)
    if cached:
        return jsonify(cached)

    # 1. Спроба через API
    api_url = f'https://steamcommunity.com/market/priceoverview/?country=UA&currency=1&appid=730&market_hash_name={item}'
    try:
        r = requests.get(api_url, timeout=10)
        api_data = r.json()
    except Exception as e:
        api_data = {'success': False, 'error': str(e)}

    if api_data.get('success') and api_data.get('lowest_price'):
        result = {
            'source': 'api',
            **api_data
        }
        set_cache(item, result)
        return jsonify(result)

    # 2. Fallback: парсинг HTML-сторінки
    page_url = f'https://steamcommunity.com/market/listings/730/{item}'
    try:
        r = requests.get(page_url, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        price_div = soup.find('span', class_='market_commodity_order_div')
        if not price_div:
            price_div = soup.find('span', class_='market_listing_price market_listing_price_with_fee')
        if price_div:
            text = price_div.get_text().strip()
            m = re.search(r'(\$[0-9.,]+)', text)
            if m:
                median = m.group(1)
                result = {
                    'source': 'html',
                    'success': True,
                    'median_price': median,
                    'volume': None
                }
                set_cache(item, result)
                return jsonify(result)
    except Exception as e:
        pass

    # 3. Якщо й так — повернути помилку
    result = {'success': False, 'error': 'No price found'}
    set_cache(item, result)
    return jsonify(result)

@app.route('/')
def index():
    return jsonify({'message': 'Steam price proxy with fallback is working'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
