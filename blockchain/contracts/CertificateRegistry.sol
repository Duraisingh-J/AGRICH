// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IRoleManager {
    function isGovernment(address user) external view returns (bool);
}

contract CertificateRegistry {

    IRoleManager public roleManager;

    struct Certificate {
        bytes32 documentHash;     // Hash of land certificate
        bool approved;            // Government approval status
        address boundWallet;      // Wallet bound after registration
    }

    // aadhaarHash => Certificate
    mapping(bytes32 => Certificate) private certificates;

    // wallet => whether already used
    mapping(address => bool) public walletUsed;

    // ================= EVENTS =================

    event CertificateApproved(
        bytes32 indexed aadhaarHash,
        bytes32 indexed documentHash
    );

    event CertificateBound(
        bytes32 indexed aadhaarHash,
        address indexed wallet
    );

    event CertificateRevoked(bytes32 indexed aadhaarHash);

    // ================= MODIFIERS =================

    modifier onlyGovernment() {
        require(
            roleManager.isGovernment(msg.sender),
            "Not Government"
        );
        _;
    }

    constructor(address _roleManager) {
        require(_roleManager != address(0), "Invalid role manager");
        roleManager = IRoleManager(_roleManager);
    }

    // =====================================================
    // GOVERNMENT FUNCTIONS
    // =====================================================

    function approveCertificate(
        bytes32 aadhaarHash,
        bytes32 documentHash
    ) external onlyGovernment {

        require(aadhaarHash != bytes32(0), "Invalid aadhaar hash");
        require(documentHash != bytes32(0), "Invalid document hash");

        Certificate storage cert = certificates[aadhaarHash];

        require(!cert.approved, "Already approved");

        certificates[aadhaarHash] = Certificate({
            documentHash: documentHash,
            approved: true,
            boundWallet: address(0)
        });

        emit CertificateApproved(aadhaarHash, documentHash);
    }

    function revokeCertificate(bytes32 aadhaarHash)
        external
        onlyGovernment
    {
        require(certificates[aadhaarHash].approved, "Not approved");

        delete certificates[aadhaarHash];

        emit CertificateRevoked(aadhaarHash);
    }

    // =====================================================
    // FARMER REGISTRATION BINDING
    // =====================================================

    function bindCertificate(
        bytes32 aadhaarHash,
        bytes32 documentHash
    ) external {

        Certificate storage cert = certificates[aadhaarHash];

        require(cert.approved, "Certificate not approved");
        require(cert.boundWallet == address(0), "Already bound");
        require(!walletUsed[msg.sender], "Wallet already used");

        require(
            cert.documentHash == documentHash,
            "Document hash mismatch"
        );

        cert.boundWallet = msg.sender;
        walletUsed[msg.sender] = true;

        emit CertificateBound(aadhaarHash, msg.sender);
    }

    // =====================================================
    // VIEW FUNCTIONS
    // =====================================================

    function isApproved(bytes32 aadhaarHash)
        external
        view
        returns (bool)
    {
        return certificates[aadhaarHash].approved;
    }

    function getBoundWallet(bytes32 aadhaarHash)
        external
        view
        returns (address)
    {
        return certificates[aadhaarHash].boundWallet;
    }

    function getDocumentHash(bytes32 aadhaarHash)
        external
        view
        returns (bytes32)
    {
        return certificates[aadhaarHash].documentHash;
    }
}