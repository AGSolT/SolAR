const EZCoin = artifacts.require("EzToken");

module.exports = function(deployer) {
  deployer.deploy(EZCoin, 1000, "EZCoin", 1, "E");
};
