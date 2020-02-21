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

function TestTwo(uint b) public view returns(bool success){
  if (b == 128){
    return false;
  }
  else{
      return true;
  }
}

function TestThree(uint c) public view returns(bool success){
  if (c == 128){
    return false;
  }
  else{
      return true;
  }
}
}
