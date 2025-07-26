from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

@app.route('/steam-price')
def get_price():
    item = request.args.get('item')
    if not item:
        return jsonify({'error': 'Item name is required'}), 400

    url = f'https://steamcommunity.com/market/priceoverview/?country=UA&currency=1&appid=730&market_hash_name={item}'
    try:
        response = requests.get(url)
        data = response.json()
        print('Steam API response:', data)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ['PORT'])  # обов'язково PORT без дефолту
    print(f'Starting server on port {port}...')
    app.run(host='0.0.0.0', port=port)
