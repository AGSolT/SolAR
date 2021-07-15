# Control Flow Graph Construcion Example
This document explains conceptually how a Control-Flow Graph (CFG) is extracted from the bytecode of a deployed contract. AGSolT relies on the <a href="https://github.com/crytic/evm_cfg_builder">evm_cfg_builder</a> library for creating a first CFG, before taking additional steps to create a Control-Dependendy Graph (CDG) and removing some superfluous notes, as explained in the accompanying <a href="https://arxiv.org/abs/2102.08864">paper</a>.

## The contract and compilation.
We follow here, the same example smart contract that was also given in the paper: a simple auction contract, which can be found in [Auction.sol](./Auction.sol):

```
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
```

When this Solidity code is fed to the compiler, it creates a bytecode object, which is shown [Auction.json](./Auction.json) and which looks something like:

```
60806040526040516103ec3803806103ec8339818101604052602081101561002657600080fd5b810190808051906020019...
```

It is this bytecode that is stored on the blockchain and which instructs the Ethereum Virtual Machine (EVM) on how to execute the relevant code.

## Opcodes
The bytecode can be interpreted as <textit>opcodes</textit>, which are stand-alone instructions for the EVM. The opcodes for the Auction smart contract are also stored in the [Auction.json](./Auction.json) file. For example, the ```6080``` at the beginning of the bytecode corresponds to the opcodes for ```PUSH 80```, meaning that the value ```80``` should be pushed to the stack. A full list of opcodes and their corresponding bytecodes can be found [here](https://ethervm.io/), or in the <a href="https://ethereum.github.io/yellowpaper/paper.pdf">Ethereum yellow paper</a>.

There are 9 opcodes which are particularly relevant for identifying nodes and branches in a CFG. The table below shows these in the opcode column, their hex value as it appears in bytecode as well as the argument(s) they consume from the stack and the output value they push onto the stack. The "JUMP"-opcode is used to jump to a different part of the bytecode for execution (indicated by the destination value). The "JUMPI"-opcode works similar to "JUMP" except that execution continues from the destination, only if the consumed bool is true, this is what creates branches in the CFG. Finally the other opcodes shown in \cref{tab:opcodes} correspond to the predicates that can control a branch; $<$, $>$, $==$ and $\neg$. Note that $\leq$, $\geq$ and $\neq$ can be represented with $\neg>$, $\neg<$ and $\neg==$ respectively.

| Hex | Opcode | Stack Input | Stack Output |
|--|--|--|--|
56 | JUMP | dest | |
57 | JUMPI | dest, bool | |
5B | JUMPDEST | | |
10 | LT | $a$, $b$ | $a<b$ |
11 | GT | $a$, $b$ | $a>b$ |
12 | SLT | $a$, $b$ | $a<b$ |
13 | SGT | $a$, $b$ | $a>b$ |
14 | EQ | $a$, $b$ | $a=b$ |
15 | ISZERO | $a$ | $a=0$ |


## From Opcodes to CFG
Three of these opcodes are of particular importance for CFG creation: ```JUMPDEST```, ```JUMP``` and ```JUMPI```. ```JUMP``` tells the EVM to jump to a different position in the bytecode (the position is consumed from the stack) and continue taking instructions from there. As such, it is a natural ending to a node, which consists of a set of instructions that are always executed together. ```JUMPI``` works similar to ```JUMP``` but consumes also a boolean value from the stack; only if this value is equal to True is the EVM instructed to jump, otherwise it will simply continue with the next instruction in the bytecode. Finally, ```JUMPDEST ``` is reserved as a location in the bytecode to which a ```JUMP``` or ```JUMPI``` can point. These three instructions form natural first and last statements for nodes in the CFG. For example, in the opcodes of the Auction smart contract, we can find the following instructions:

```
JUMPDEST
CALLVALUE
DUP1
ISZERO
PUSH2 0x66
JUMPI
PUSH1 0x0
DUP1
REVERT
```

This naturally leads to three different nodes, each with their own instructions:

```
(1)
JUMPDEST
CALLVALUE
DUP1
ISZERO
PUSH2 0x66
JUMPI

(2)
JUMPDEST
POP
PUSH2 0x6f
PUSH2 0x17f
JUMP

(3)
PUSH1 0x0
DUP1
REVERT
```

The first node, is the parent node, the second node contains the opcodes that are stored location ```0x66```, which the EVM is instructed to jump to if the boolean on the stack is true, the third node is where the EVM will continue if the boolean on the stack was false and there was no jump needed.

## Disclaimer
Please note that AGSolT uses a Control <emph>Dependency</emph> Graph and not a Control <emph>Flow</emph> Graph. Additionally, a number of nodes are merged, to minimise the number of irrelevant branches and increase the effectiveness of guided search approaches.
