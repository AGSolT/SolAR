pragma solidity 0.5.12;

contract Auction {
    address payable public Seller;
    address payable public Frontrunner;
    uint public HighBid;
    uint public CloseTime;

    constructor (uint _CloseTime) payable public {
        Seller = msg.sender;
        Frontrunner = msg.sender;
        HighBid = msg.value;
        CloseTime = _CloseTime;
    }

    function Bid() payable public {
        require(msg.value > HighBid);
        Frontrunner.transfer(HighBid);
        HighBid = msg.value;
        Frontrunner = msg.sender;
    }

    function Claim() external{
        require(block.timestamp > CloseTime);
        // Implement ownership transfer.
        selfdestruct(Seller);
    }
}
