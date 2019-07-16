// This script connects to the Ethereum simulator that is listening at the specified port and and writes the accounts that can be used to deploy and interact with the smart contract to the specified file.
const Web3 = require('web3')
const fs = require('fs');
const args = require('minimist')(process.argv.slice(2));

const port = args.ETH_port;
const max_accounts = args.max_accounts;
const accounts_file_location = args.accounts_file_location;

const web3 = new Web3(new Web3.providers.HttpProvider(port));

web3.eth.getAccounts().then(function(accounts){
  if (accounts.length<max_accounts){
    console.log(`There are fewer accounts on the Blockchain than the specified number of max_accounts.\nmax_accounts: ${max_accounts}\nAccounts on Blockchain: ${accounts.length}\nProceeding with all accounts on the Blockchain...`)
    var nr_of_accounts = accounts.length;
  }
  else{
    var nr_of_acounts = max_accounts;
  }
  fs.writeFile(accounts_file_location, accounts.slice(0, nr_of_accounts), function(err){
    if(err){
      return console.log(err)
    }
    console.log(`Accounts written succesfully to: ${accounts_file_location}`)
  });
});
