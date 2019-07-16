pragma solidity ^0.5.0;

contract TestContract{

constructor() public {
}

function TestOne(uint a) public view returns(bool success){
  if (a == 128){
    return false;
  }
  else{
      return true;
  }
}
}
