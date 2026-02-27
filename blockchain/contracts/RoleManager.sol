// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract RoleManager {

    // =========================
    // ENUMS
    // =========================

    enum Role {
        NONE,
        FARMER,
        DISTRIBUTOR,
        RETAILER,
        CONSUMER,
        GOVERNMENT,
        AUDITOR
    }

    // =========================
    // STATE VARIABLES
    // =========================

    address public superAdmin; // GovernmentAuthority

    mapping(address => Role) private roles;
    mapping(address => bool) private verified;

    // =========================
    // EVENTS
    // =========================

    event RoleAssigned(address indexed user, Role role);
    event RoleRemoved(address indexed user);
    event VerificationUpdated(address indexed user, bool status);
    event SuperAdminTransferred(address indexed oldAdmin, address indexed newAdmin);

    // =========================
    // MODIFIERS
    // =========================

    modifier onlySuperAdmin() {
        require(msg.sender == superAdmin, "Not authorized");
        _;
    }

    modifier onlyExistingUser(address user) {
        require(roles[user] != Role.NONE, "User not registered");
        _;
    }

    // =========================
    // CONSTRUCTOR
    // =========================

    constructor(address _superAdmin) {
        require(_superAdmin != address(0), "Invalid admin address");
        superAdmin = _superAdmin;
        roles[_superAdmin] = Role.GOVERNMENT;
        verified[_superAdmin] = true;
    }

    // =========================
    // ROLE MANAGEMENT
    // =========================

    function assignRole(address user, Role role) external onlySuperAdmin {
        require(user != address(0), "Invalid address");
        require(role != Role.NONE, "Invalid role");

        roles[user] = role;
        emit RoleAssigned(user, role);
    }

    function removeRole(address user) external onlySuperAdmin onlyExistingUser(user) {
        roles[user] = Role.NONE;
        verified[user] = false;
        emit RoleRemoved(user);
    }

    function transferSuperAdmin(address newAdmin) external onlySuperAdmin {
        require(newAdmin != address(0), "Invalid address");

        address oldAdmin = superAdmin;

        superAdmin = newAdmin;
        roles[newAdmin] = Role.GOVERNMENT;
        verified[newAdmin] = true;

        emit SuperAdminTransferred(oldAdmin, newAdmin);
    }

    // =========================
    // VERIFICATION CONTROL
    // =========================

    function setVerification(address user, bool status)
        external
        onlySuperAdmin
        onlyExistingUser(user)
    {
        verified[user] = status;
        emit VerificationUpdated(user, status);
    }

    // =========================
    // VIEW FUNCTIONS
    // =========================

    function getRole(address user) external view returns (Role) {
        return roles[user];
    }

    function isVerified(address user) external view returns (bool) {
        return verified[user];
    }

    function isFarmer(address user) external view returns (bool) {
        return roles[user] == Role.FARMER;
    }

    function isDistributor(address user) external view returns (bool) {
        return roles[user] == Role.DISTRIBUTOR;
    }

    function isRetailer(address user) external view returns (bool) {
        return roles[user] == Role.RETAILER;
    }

    function isGovernment(address user) external view returns (bool) {
        return roles[user] == Role.GOVERNMENT;
    }
}