const MemoryArrayBuildingCheap = artifacts.require("MemoryArrayBuildingCheap");

module.exports = function(deployer) {
  deployer.deploy(MemoryArrayBuildingCheap);
};
