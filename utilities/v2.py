from web3 import Web3
from eth_account import Account
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()


class UniswapV2Router:
    # Uniswap V2 Router ABI - 只包含我们需要的swapExactTokensForTokens函数
    ROUTER_ABI = [
        {
            "inputs": [
                {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                {"internalType": "address[]", "name": "path", "type": "address[]"},
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"}
            ],
            "name": "swapExactTokensForTokens",
            "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]

    # 与V3相同的ERC20 ABI
    ERC20_ABI = [
        {
            "inputs": [
                {"name": "spender", "type": "address"},
                {"name": "amount", "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [{"name": "account", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]

    def __init__(self):
        # 初始化Web3连接和合约
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('SEPOLIA_RPC')))
        self.router_address = Web3.to_checksum_address(os.getenv('SEPOLIA_ROUTER_V2'))
        self.router_contract = self.w3.eth.contract(
            address=self.router_address,
            abi=self.ROUTER_ABI
        )
        self.account = Account.from_key(os.getenv('PRIVATE_KEY'))
        print(f"Initialized with account: {self.account.address}")

    def swap_exact_tokens_for_tokens(self, token_path: List[str], amount_in: int = 0) -> dict:
        """
        执行代币兑换交易
        :param token_path: 代币路径列表
        :param amount_in: 输入代币数量
        :return: 交易结果字典
        """
        if len(token_path) < 2:
            raise ValueError("Token path must contain at least 2 tokens")

        # 将所有地址转换为checksum格式
        token_path = [Web3.to_checksum_address(addr) for addr in token_path]

        if amount_in > 0:
            # 首先授权路由合约使用输入代币
            token_contract = self.w3.eth.contract(
                address=token_path[0],
                abi=self.ERC20_ABI
            )

            approve_tx = token_contract.functions.approve(
                self.router_address,
                amount_in
            ).build_transaction({
                'from': self.account.address,
                'gas': 100000,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'maxFeePerGas': self.w3.eth.gas_price * 2,
                'maxPriorityFeePerGas': self.w3.eth.gas_price
            })

            signed_approve = self.w3.eth.account.sign_transaction(approve_tx, self.account.key)
            self.w3.eth.send_raw_transaction(signed_approve.rawTransaction)
            self.w3.eth.wait_for_transaction_receipt(signed_approve.hash)

        # 计算交易截止时间（当前时间 + 20分钟）
        deadline = self.w3.eth.get_block('latest').timestamp + 1200

        # 构建兑换交易
        swap_tx = self.router_contract.functions.swapExactTokensForTokens(
            amount_in,  # 输入金额
            0,  # 最小输出金额 (这里设为0，实际使用时应该设置滑点保护)
            token_path,  # 代币路径
            self.account.address,  # 接收地址
            deadline  # 交易截止时间
        ).build_transaction({
            'from': self.account.address,
            'gas': 300000,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'maxFeePerGas': self.w3.eth.gas_price * 2,
            'maxPriorityFeePerGas': self.w3.eth.gas_price,
            'value': 0
        })

        # 签名并发送交易
        signed_swap = self.w3.eth.account.sign_transaction(swap_tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_swap.rawTransaction)
        print('https://sepolia.etherscan.io/tx/' + tx_hash.hex())
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        return {
            'transaction_hash': receipt['transactionHash'].hex(),
            'status': receipt['status'],
            'gas_used': receipt['gasUsed'],
            'block_number': receipt['blockNumber']
        }


def main():
    router = UniswapV2Router()

    # 定义交易路径
    token_path = [
        os.getenv('SEPOLIA_USDC'),
        os.getenv('SEPOLIA_UNI')
    ]

    amount_in = 1000000  # 输入金额，根据代币精度调整

    try:
        result = router.swap_exact_tokens_for_tokens(token_path, amount_in)
        print(f"Transaction hash: {result['transaction_hash']}")
    except Exception as e:
        print(f"Transaction failed: {str(e)}")


if __name__ == "__main__":
    main()