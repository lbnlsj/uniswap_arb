from flask import Flask, render_template, request, jsonify
import random
from web3 import Web3

app = Flask(__name__)

DEX_PROTOCOLS = [
    {'name': 'Uniswap V2', 'pools': ['0.3%']},
    {'name': 'Uniswap V3', 'pools': ['0.01%', '0.05%', '0.3%', '1%']},
    {'name': 'SushiSwap', 'pools': ['0.3%']},
    {'name': 'PancakeSwap', 'pools': ['0.25%']},
    {'name': 'Curve', 'pools': ['0.04%']},
    {'name': 'Balancer', 'pools': ['0.3%', '1%']}
]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/calculate_route', methods=['POST'])
def calculate_route():
    try:
        rpc_url = request.form.get('rpcUrl')
        web3 = Web3(Web3.HTTPProvider(rpc_url))
        chain_id = web3.eth.chain_id if web3.is_connected() else 1  # 默认使用以太坊主网
        token_type = request.form.get('tokenType', 'native')
        amount = float(request.form.get('tradeAmount', 1.0))

        # 根据chain_id识别网络原生代币
        native_tokens = {
            1: 'ETH',
            56: 'BNB',
            137: 'MATIC',
            42161: 'ETH',
            10: 'ETH'
        }

        token_symbol = native_tokens.get(chain_id, 'ETH') if token_type == 'native' else 'ERC20'

        # 生成随机路由路径
        route = generate_random_route()

        result = {
            'inputToken': token_symbol,
            'inputAmount': amount,
            'outputAmount': calculate_output_amount(amount, route),
            'estimatedGas': random.randint(80000, 500000),
            'priceImpact': random.uniform(0.001, 0.02) * 100,
            'route': route
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


def generate_random_route():
    route = []
    num_hops = random.randint(1, 3)  # 随机1-3跳路由

    used_protocols = set()
    for _ in range(num_hops):
        # 随机选择未使用的协议
        available_protocols = [p for p in DEX_PROTOCOLS if p['name'] not in used_protocols]
        if not available_protocols:
            break

        protocol = random.choice(available_protocols)
        used_protocols.add(protocol['name'])

        route.append({
            'protocol': protocol['name'],
            'pool': random.choice(protocol['pools'])
        })

    return route


def calculate_output_amount(amount, route):
    # 基于路由计算输出金额
    output = amount
    for hop in route:
        impact = random.uniform(0.997, 0.999)  # 每跳0.1-0.3%的滑点
        output *= impact
    return output


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=7200)