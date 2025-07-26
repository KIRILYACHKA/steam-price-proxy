from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"message": "✅ Steam price proxy is working"}), 200

@app.route('/steam-price')
def get_price():
    item = request.args.get('item')
    if not item:
        return jsonify({'error': 'Item name is required'}), 400

    url = f'https://steamcommunity.com/market/priceoverview/?country=UA&currency=1&appid=730&market_hash_name={item}'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'application/json',
        'Referer': 'https://steamcommunity.com/market/',
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        content_type = response.headers.get('Content-Type', '')

        if 'application/json' not in content_type:
            return jsonify({
                'error': 'Steam returned non-JSON response',
                'content_type': content_type,
                'raw': response.text[:500]  # Показати частину HTML якщо треба
            }), 500

        data = response.json()

        # Steam може повертати success=true, але без даних
        if not data.get("lowest_price") and not data.get("median_price"):
            return jsonify({
                'warning': 'Steam returned success=true, but no price data',
                'steam_response': data
            }), 200

        return jsonify(data)

    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Request failed', 'details': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Something went wrong', 'details': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f'Starting server on port {port}...')
    app.run(host='0.0.0.0', port=port)
