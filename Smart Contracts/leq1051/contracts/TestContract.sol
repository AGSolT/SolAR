pragma solidity ^0.5.0;

contract TestContract{

constructor() public {
}

function TestOne(uint a) public view returns(bool success){
  if (a < 13){
    return false;
  }
  else{
      return true;
  }
}

function TestTwo(uint b) public view returns(bool success){
  if (b < 13){
    return false;
  }
  else{
      return true;
  }
}

function TestThree(uint c) public view returns(bool success){
  if (c < 13){
    return false;
  }
  else{
      return true;
  }
}

function TestFour(uint d) public view returns(bool success){
  if (d < 13){
    return false;
  }
  else{
      return true;
  }
}

function TestFive(uint e) public view returns(bool success){
  if (e < 13){
    return false;
  }
  else{
      return true;
  }
}
}
