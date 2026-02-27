import { ethers } from "hardhat";

async function main() {
  const provider = ethers.provider;
  const block = await provider.getBlockNumber();
  console.log("Current block:", block);
}

main();