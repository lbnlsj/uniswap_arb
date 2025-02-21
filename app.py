from flask import Flask, request, render_template, jsonify
from web3 import Web3
import os
from utilities.v3 import UniswapV3Router
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

# 网络配置
NETWORK_CONFIG = {
    'sepolia': {
        'rpc': os.getenv('SEPOLIA_RPC'),
        'router': os.getenv('SEPOLIA_ROUTER')
    },
    'mainnet': {
        'rpc': os.getenv('ETH_RPC'),
        'router': os.getenv('ETH_ROUTER', '0xE592427A0AEce92De3Edee1F18E0157C05861564')  # Mainnet Router
    }
}

# 默认的交易费率（0.3%）
DEFAULT_FEE = 3000

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/swap', methods=['POST'])
def execute_swap():
    try:
        data = request.json
        network = data.get('network', 'sepolia')
        token_path = data.get('tokenPath', [])
        amount_in = int(data.get('amountIn', 0))
        private_key = data.get('privateKey')

        # 验证输入
        if not all([network, token_path, amount_in, private_key]):
            return jsonify({'error': '缺少必要参数'}), 400

        if len(token_path) < 2:
            return jsonify({'error': '代币路径必须包含至少2个代币'}), 400

        # 使用默认交易费率
        fees = [DEFAULT_FEE] * (len(token_path) - 1)

        # 设置环境变量
        os.environ['PRIVATE_KEY'] = private_key
        os.environ[f'{network.upper()}_RPC'] = NETWORK_CONFIG[network]['rpc']
        os.environ[f'{network.upper()}_ROUTER'] = NETWORK_CONFIG[network]['router']

        # 初始化路由器并执行交易
        router = UniswapV3Router()
        result = router.swap_exact_input(token_path, fees, amount_in)

        return jsonify({
            'success': True,
            'transaction': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3453, debug=True)