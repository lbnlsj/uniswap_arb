from web3 import Web3
from eth_account import Account
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()


class UniswapV3Router:
    ROUTER_ABI = [
        {
            "inputs": [
                {
                    "components": [
                        {"internalType": "bytes", "name": "path", "type": "bytes"},
                        {"internalType": "address", "name": "recipient", "type": "address"},
                        {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                        {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"}
                    ],
                    "internalType": "struct ISwapRouter.ExactInputParams",
                    "name": "params",
                    "type": "tuple"
                }
            ],
            "name": "exactInput",
            "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
            "stateMutability": "payable",
            "type": "function"
        }
    ]

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
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('SEPOLIA_RPC')))
        self.router_address = Web3.to_checksum_address(os.getenv('SEPOLIA_ROUTER'))
        self.router_contract = self.w3.eth.contract(
            address=self.router_address,
            abi=self.ROUTER_ABI
        )
        self.account = Account.from_key(os.getenv('PRIVATE_KEY'))
        print(f"Initialized with account: {self.account.address}")

    def encode_path(self, token_addresses: List[str], fees: List[int]) -> bytes:
        path = b''
        for i in range(len(token_addresses) - 1):
            path += Web3.to_bytes(hexstr=token_addresses[i])
            path += fees[i].to_bytes(3, 'big')
        path += Web3.to_bytes(hexstr=token_addresses[-1])
        return path

    def swap_exact_input(self, token_path: List[str], fees: List[int], amount_in: int = 0) -> dict:
        if len(token_path) < 2 or len(fees) != len(token_path) - 1:
            raise ValueError("Invalid path or fees length")

        encoded_path = self.encode_path(token_path, fees)

        if amount_in > 0:
            token_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_path[0]),
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

        params = {
            'path': encoded_path,
            'recipient': self.account.address,
            'amountIn': amount_in,
            'amountOutMinimum': 0
        }

        swap_tx = self.router_contract.functions.exactInput(params).build_transaction({
            'from': self.account.address,
            'gas': 30000000,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'maxFeePerGas': self.w3.eth.gas_price * 2,
            'maxPriorityFeePerGas': self.w3.eth.gas_price,
            'value': 0
        })

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
    router = UniswapV3Router()

    token_path = [
        os.getenv('SEPOLIA_USDC'),
        os.getenv('SEPOLIA_UNI'),
        os.getenv('SEPOLIA_WETH'),
        os.getenv('SEPOLIA_USDC')
    ]

    fees = [3000] * (len(token_path) - 1)
    amount_in = 1000000

    try:
        result = router.swap_exact_input(token_path, fees, amount_in)
        print(f"Transaction hash: {result['transaction_hash']}")
    except Exception as e:
        print(f"Transaction failed: {str(e)}")


if __name__ == "__main__":
    main()