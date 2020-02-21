pragma solidity ^0.5.0;

contract TestContract{

constructor() public {
}

function TestOne(uint a, uint b, uint c, uint d, uint e) public view returns(bool success){
  uint ans = 0;
  if (a < 13){
    ans = ans + 1;
  }
  else if (b < 13){
    ans = ans + 1;
  }
  else if (c < 13){
    ans = ans + 1;
  }
  else if (d < 13){
    ans = ans + 1;
  }
  else if (e < 13){
    ans = ans + 1;
  }
  return true;
}
}
