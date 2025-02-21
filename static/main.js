document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('swapForm');
    const addTokenBtn = document.getElementById('addToken');
    const tokenPathContainer = document.getElementById('tokenPathContainer');
    const loadingIndicator = document.querySelector('.loading');
    const resultContainer = document.getElementById('result');

    // 区块浏览器URL配置
    const EXPLORER_URLS = {
        'sepolia': 'https://sepolia.etherscan.io/tx/',
        'mainnet': 'https://etherscan.io/tx/'
    };

    // 显示移除按钮
    function updateRemoveButtons() {
        const tokenInputs = tokenPathContainer.querySelectorAll('.token-input');
        tokenInputs.forEach((input, index) => {
            const removeBtn = input.querySelector('.remove-token');
            if (tokenInputs.length > 2) {
                removeBtn.style.display = 'block';
            } else {
                removeBtn.style.display = 'none';
            }
        });
    }

    // 初始化移除按钮状态
    updateRemoveButtons();

    // 添加新的代币输入框
    addTokenBtn.addEventListener('click', function() {
        const tokenInputs = tokenPathContainer.querySelectorAll('.token-input');
        if (tokenInputs.length < 5) { // 限制最多5个代币
            const newTokenInput = document.createElement('div');
            newTokenInput.className = 'token-input';
            newTokenInput.innerHTML = `
                <input type="text" class="form-control" placeholder="代币地址 ${tokenInputs.length + 1}" required>
                <button type="button" class="btn btn-danger remove-token">移除</button>
            `;
            tokenPathContainer.appendChild(newTokenInput);

            // 绑定移除按钮事件
            const removeBtn = newTokenInput.querySelector('.remove-token');
            removeBtn.addEventListener('click', function() {
                newTokenInput.remove();
                updateRemoveButtons();
            });

            updateRemoveButtons();
        }
    });

    // 为现有的移除按钮添加事件监听
    document.querySelectorAll('.remove-token').forEach(btn => {
        btn.addEventListener('click', function() {
            btn.closest('.token-input').remove();
            updateRemoveButtons();
        });
    });

    // 格式化交易结果
    function formatTransactionResult(result, network) {
        const explorerUrl = EXPLORER_URLS[network] + result.transaction_hash;
        return {
            '交易哈希': result.transaction_hash,
            '区块浏览器链接': `<a href="${explorerUrl}" target="_blank" class="result-link">${explorerUrl}</a>`,
            '状态': result.status ? '成功' : '失败',
            '使用的gas': result.gas_used,
            '区块号': result.block_number
        };
    }

    // 处理表单提交
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        loadingIndicator.style.display = 'block';
        resultContainer.textContent = '';

        // 收集表单数据
        const tokenInputs = tokenPathContainer.querySelectorAll('input');
        const tokenPath = Array.from(tokenInputs).map(input => input.value);
        const network = document.getElementById('network').value;

        const requestData = {
            network: network,
            privateKey: document.getElementById('privateKey').value,
            amountIn: document.getElementById('amountIn').value,
            tokenPath: tokenPath
        };

        try {
            const response = await fetch('/api/swap', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            const result = await response.json();

            if (result.success) {
                const formattedResult = formatTransactionResult(result.transaction, network);
                // 使用innerHTML来支持链接的HTML
                resultContainer.innerHTML = Object.entries(formattedResult)
                    .map(([key, value]) => `${key}: ${value}`)
                    .join('\n');
            } else {
                resultContainer.textContent = `错误: ${result.error}`;
            }
        } catch (error) {
            resultContainer.textContent = `错误: ${error.message}`;
        } finally {
            loadingIndicator.style.display = 'none';
        }
    });

    // 当网络改变时保持默认私钥
    document.getElementById('network').addEventListener('change', function() {
        document.getElementById('privateKey').value = 'f9c182a372a722fea5a61af35566a140fdd8106180c29fd0b69bb8e3e06c4f5a';
    });
});

// 验证以太坊地址的辅助函数
function isValidAddress(address) {
    return /^0x[a-fA-F0-9]{40}$/.test(address);
}