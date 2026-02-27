require("@nomicfoundation/hardhat-toolbox");

module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  networks: {
    besu: {
      url: "http://127.0.0.1:8545",
      chainId: 1337,
      accounts: [
        "0x23c8f49038f433eae3821e02a5c6b2010e937aa3bb6b5b328f57f84ab2877845"
      ]
    }
  }
};