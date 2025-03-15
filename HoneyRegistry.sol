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
        // Convert batchId to string
        string memory batchIdString = uintToString(batchId);
        
        // Concatenate strings
        return string(abi.encodePacked(origin, "-", batchIdString));
    }
    
    function uintToString(uint256 value) internal pure returns (string memory) {
        // Handle zero case
        if (value == 0) {
            return "0";
        }
        
        // Calculate length of result
        uint256 temp = value;
        uint256 digits;
        while (temp != 0) {
            digits++;
            temp /= 10;
        }
        
        // Create byte array of appropriate length
        bytes memory buffer = new bytes(digits);
        
        // Fill buffer from right to left
        while (value != 0) {
            digits--;
            buffer[digits] = bytes1(uint8(48 + uint256(value % 10)));
            value /= 10;
        }
        
        return string(buffer);
    }
    
    function getVerificationToken(uint256 batchId) public view returns (string memory) {
        return honeyBatches[batchId].verificationToken;
    }
}