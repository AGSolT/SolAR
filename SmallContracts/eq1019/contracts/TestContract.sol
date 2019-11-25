pragma solidity ^0.5.0;

contract TestContract{

constructor() public {
}

function TestOne(uint a, uint b, uint c, uint d, uint e, uint f, uint g, uint h, uint i) public view returns(bool success){
  uint ans = 0;
  if (a == 128){
    ans = ans + 1;
  }
  else if (b == 128){
    ans = ans + 1;
  }
  else if (c == 128){
    ans = ans + 1;
  }
  else if (d == 128){
    ans = ans + 1;
  }
  else if (e == 128){
    ans = ans + 1;
  }
  else if (f == 128){
    ans = ans + 1;
  }
  else if (g == 128){
    ans = ans + 1;
  }
  else if (h == 128){
    ans = ans + 1;
  }
  else if (i == 128){
    ans = ans + 1;
  }
}
return true;
}
