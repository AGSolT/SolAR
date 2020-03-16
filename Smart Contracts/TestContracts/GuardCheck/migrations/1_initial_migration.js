const Migrations = artifacts.require("GuardCheck");

module.exports = function(deployer) {
  deployer.deploy(GuardCheck);
};
