# 🌾 AGRICHAIN – Blockchain Layer (Permissioned Network)

## 📌 Overview

The AGRICHAIN Blockchain Layer is a permissioned blockchain network built using:

- **Hyperledger Besu**
- **IBFT (Istanbul Byzantine Fault Tolerance) Consensus**
- **4 Validator Nodes**
- **Solidity Smart Contracts**

This layer provides:

- Immutable role management
- On-chain certificate registry
- Secure ownership validation
- Tamper-proof audit trail

The blockchain acts as the **trust backbone** of the AGRICHAIN platform.

---

# 🏗 Network Architecture

FastAPI Backend → Web3 RPC → Besu Network (IBFT)

The mobile application never directly connects to the blockchain.
All blockchain interactions are handled by the backend.

---

# 🔐 Consensus Mechanism – IBFT

We use **IBFT (Istanbul Byzantine Fault Tolerance)** consensus because:

- Fast block finality
- No mining required
- Low latency
- Suitable for enterprise permissioned systems
- Fault tolerance (with 4 validators, tolerates 1 faulty node)

### Validator Nodes

- Validator Node 1
- Validator Node 2
- Validator Node 3
- Validator Node 4

Each node:
- Participates in consensus
- Signs blocks
- Maintains full ledger state

---

# 📜 Smart Contracts Implemented

## 1️⃣ RoleManager.sol

### Purpose

Manages role-based permissions on-chain.

### Supported Roles

- Farmer
- Distributor
- Retailer
- Government Authority

### Capabilities

- Assign role to wallet address
- Revoke role
- Verify role before blockchain action
- Ensure only authorized entities perform specific actions

### Why On-Chain Role Management?

- Prevents unauthorized actors
- Provides transparent role verification
- Immutable record of authority

---

## 2️⃣ CertificateRegistry.sol

### Purpose

Stores and verifies agricultural certifications on-chain.

### Capabilities

- Register certification hash (IPFS CID or document hash)
- Link certificate to batch or farmer
- Verify certificate authenticity
- Prevent duplicate or fake certifications

### Stored Data

- Certificate ID
- Owner address
- Metadata hash (IPFS)
- Timestamp
- Issuer address

This ensures:
- Tamper-proof certification validation
- Transparent quality verification
- Trust between supply chain participants

---

# 🔄 Backend Integration

The backend connects using:

- Web3.py
- RPC endpoint
- Contract ABI
- Contract address

Core interaction flow:

1. Backend validates user (JWT + RBAC)
2. Backend verifies wallet role (via RoleManager)
3. Backend submits transaction
4. Blockchain emits event
5. Backend listener updates database

---

# 📡 Event-Driven Design

Smart contracts emit structured events.

Examples:

- RoleAssigned
- RoleRevoked
- CertificateRegistered

Backend event listener:

- Listens via RPC
- Stores events in PostgreSQL
- Ensures exactly-once processing
- Retries failed event handling
- Prevents duplicate processing

This guarantees reliable synchronization between blockchain and backend.

---

# 🧠 Design Principles

## 1️⃣ Blockchain as Trust & Audit Layer

Blockchain stores:

- Role authority
- Certificate proofs
- Immutable transaction records

## 2️⃣ Database as Operational Layer

PostgreSQL stores:

- User profiles
- Batch lifecycle
- Current system state

Heavy queries are not performed on-chain.

---

# 🛡 Security Model

- Permissioned network (restricted validators)
- Wallet-based identity
- On-chain role verification
- No public mining
- Immutable certificate records
- Backend-enforced access control

Mobile clients cannot access blockchain directly.

---

# ⚙ Environment Variables (Blockchain)
WEB3_RPC_URL
ROLE_MANAGER_CONTRACT_ADDRESS
CERTIFICATE_REGISTRY_CONTRACT_ADDRESS
CONTRACT_ABI_PATH
BLOCKCHAIN_DEFAULT_SENDER
ENABLE_BLOCKCHAIN_LISTENER


---

# 🚀 Deployment Steps (Summary)

1️⃣ Start Besu validator nodes  
2️⃣ Deploy RoleManager.sol  
3️⃣ Deploy CertificateRegistry.sol  
4️⃣ Store contract addresses in backend configuration  
5️⃣ Start backend and verify RPC connectivity  

---

# 📊 Current Status

- 4-node IBFT network operational
- RoleManager contract deployed
- CertificateRegistry contract deployed
- Backend Web3 integration complete
- Event listener active
- Durable blockchain event persistence implemented

---

# 🎯 Purpose in AGRICHAIN

The blockchain layer ensures:

- Trusted identity management
- Authentic certificate verification
- Transparent governance
- Immutable audit trail

It forms the decentralized trust infrastructure for the AGRICHAIN ecosystem.
