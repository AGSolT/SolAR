pragma solidity ^0.4.20;

contract MemoryArrayBuildingCheap {

    struct Item {
        string name;
        string category;
        address owner;
        uint32 zipcode;
        uint32 price;
    }

    Item[] public items;

    mapping(address => uint) public ownerItemCount;

    function getItemsbyOwner(address _owner) public view returns (uint[]) {
        uint[] memory result = new uint[](ownerItemCount[_owner]);

        uint counter = 0;
        for (uint i = 0; i < items.length; i++) {
            if (items[i].owner == _owner) {
                result[counter] = i;
                counter++;
            }
        }
        return result;
    }

    function initialize(address _add1, address _add2) public {
        Item memory tempItem = Item("test1", "house", _add1, 80331, 212);
        items.push(tempItem);
        ownerItemCount[_add1]++;

        tempItem = Item("test2", "house", _add2, 80331, 212);
        items.push(tempItem);
        ownerItemCount[_add2]++;

        tempItem = Item("test3", "house", _add1, 80331, 212);
        items.push(tempItem);
        ownerItemCount[_add1]++;

        tempItem = Item("test4", "house", _add2, 80331, 212);
        items.push(tempItem);
        ownerItemCount[_add2]++;

        tempItem = Item("test5", "house", _add2, 80331, 212);
        items.push(tempItem);
        ownerItemCount[_add2]++;

        tempItem = Item("test6", "house", _add2, 80331, 212);
        items.push(tempItem);
        ownerItemCount[_add2]++;

        tempItem = Item("test7", "house", _add2, 80331, 212);
        items.push(tempItem);
        ownerItemCount[_add2]++;

        tempItem = Item("test8", "house", _add2, 80331, 212);
        items.push(tempItem);
        ownerItemCount[_add2]++;

        tempItem = Item("test9", "house", _add2, 80331, 212);
        items.push(tempItem);
        ownerItemCount[_add2]++;

        tempItem = Item("test10", "house", _add2, 80331, 212);
        items.push(tempItem);
        ownerItemCount[_add2]++;
    }
}
