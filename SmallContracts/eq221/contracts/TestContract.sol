pragma solidity ^0.5.0;

contract TestContract{

constructor() public {
}

function TestOne(bool a) public view returns(bool success){
  if (a){
    return false;
  }
  else{
      return true;
  }
}
}
