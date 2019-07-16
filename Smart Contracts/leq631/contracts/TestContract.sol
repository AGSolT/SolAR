pragma solidity ^0.5.0;

contract TestContract{

constructor() public {
}

function TestOne(uint a, uint b) public view returns(bool success){
  if (a < b){
    return false;
  }
  else{
      return true;
  }
}

function TestTwo(uint c, uint d) public view returns(bool success){
  if (c < d){
    return false;
  }
  else{
      return true;
  }
}

function TestThree(uint e, uint f) public view returns(bool success){
  if (e < f){
    return false;
  }
  else{
      return true;
  }
}}
