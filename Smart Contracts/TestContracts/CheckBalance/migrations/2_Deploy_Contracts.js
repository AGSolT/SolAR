const CheckBalance = artifacts.require("CheckBalance");

module.exports = function(deployer) {
  deployer.deploy(CheckBalance);
};
