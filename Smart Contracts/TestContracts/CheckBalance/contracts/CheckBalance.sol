pragma solidity ^0.4.21;

contract CheckBalance{

  function balance(address addr) payable public returns(uint bal){
    return addr.balance;
  }
}
