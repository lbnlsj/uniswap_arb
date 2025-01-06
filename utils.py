import time
from web3 import Web3
from uniswap import Uniswap

# 设置环境变量
infura_url = "https://goerli.infura.io/v3/YOUR_INFURA_PROJECT_ID"  # 你自己的Infura测试网URL
private_key = "YOUR_PRIVATE_KEY"  # 你的钱包私钥
address = "YOUR_WALLET_ADDRESS"  # 你的钱包地址

# 初始化Web3和Uniswap客户端
web3 = Web3(Web3.HTTPProvider(infura_url))
uniswap = Uniswap(address=address, private_key=private_key, provider=web3)

# 设置交易参数
token_in = "0x5f2f98f0f7d11849134db4a9a4d18d0c6d12a9f4"  # 以太坊测试网的一个代币地址（例如 DAI）
token_out = "0x5b1b402c2c297b5d0c062015ed0429f46e40c7f3"  # 以太坊测试网的另一个代币地址（例如 USDC）

# 获取代币地址
token_in_address = web3.to_checksum_address(token_in)
token_out_address = web3.to_checksum_address(token_out)


# 获取代币的当前价格
def get_price(token_in_address, token_out_address):
    price = uniswap.get_price(token_in_address, token_out_address)
    print(f"当前价格：1 {token_in} = {price} {token_out}")
    return price


# 计算套利机会
def check_arbitrage():
    price_in_to_out = get_price(token_in_address, token_out_address)
    price_out_to_in = get_price(token_out_address, token_in_address)

    if price_in_to_out > price_out_to_in:
        print("发现套利机会！")
        return True
    else:
        print("没有套利机会。")
        return False


# 执行套利交易
def execute_arbitrage():
    if check_arbitrage():
        amount_in = web3.to_wei(0.1, 'ether')  # 交易金额（例如 0.1 ETH）

        # 执行交易
        try:
            tx = uniswap.make_trade(token_in_address, token_out_address, amount_in, slippage=0.5)
            print(f"交易已提交！交易哈希：{tx.hex()}")
            receipt = web3.eth.waitForTransactionReceipt(tx)
            print(f"交易成功，交易哈希：{receipt.transactionHash.hex()}")
        except Exception as e:
            print(f"交易失败：{e}")
    else:
        print("没有套利机会，跳过交易。")


# 定时检查套利机会并执行交易
def main():
    while True:
        execute_arbitrage()
        time.sleep(60)  # 每分钟检查一次套利机会


if __name__ == "__main__":
    main()
