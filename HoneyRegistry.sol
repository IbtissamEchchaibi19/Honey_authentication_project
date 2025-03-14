// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
contract HoneyRegistry {
    struct HoneyBatch {
        string origin;
        uint256 timestamp;
        string verificationToken;
    }
    mapping(uint256 => HoneyBatch) public honeyBatches;
    event HoneyRegistered(uint256 batchId, string verificationToken);
    function registerHoney(uint256 batchId, string memory origin) public {
        require(honeyBatches[batchId].timestamp == 0, "Batch already registered");
        string memory token = generateVerificationToken(batchId, origin);
        honeyBatches[batchId] = HoneyBatch(origin, block.timestamp, token);
        emit HoneyRegistered(batchId, token);
    }
    function generateVerificationToken(uint256 batchId, string memory origin) internal pure returns (string memory) {
        return string(abi.encodePacked(origin, "-", batchId));
    }
    function getVerificationToken(uint256 batchId) public view returns (string memory) {
        return honeyBatches[batchId].verificationToken;
    }

    
}
