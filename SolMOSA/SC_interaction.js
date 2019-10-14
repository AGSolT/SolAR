// This script connects to the Ethereum simulator that is listening at the specified port and deploys the contract and calls it's methods following the --methods argument.
const Web3 = require('web3')
const fs = require('fs');
const Debug = require('web3-eth-debug').Debug;
const args = require('minimist')(process.argv.slice(2));
const options = {
    transactionConfirmationBlocks: 1,
}

const port = args.ETH_port;
const web3 = new Web3(new Web3.providers.HttpProvider(port), null, options);
const debug = new Debug(new Web3.providers.HttpProvider(port), null, options);

const methods = eval(args.methods);
const contract_Abi = eval(args.abi);
const bytecode = eval(args.bytecode);

const contract = new web3.eth.Contract(contract_Abi);
contract.transactionConfirmationBlocks = 1;

async function runTest(){
  var method;
  var input_args;
  var from;
  var deployed;
  var constHash;
  var tx;
  var txTrace;
  var constTrace;
  var constPos;
  var gas;
  var ans = [];
  var returnvals = [];

  for (var i = 0; i < methods.length; i++){
    method = methods[i];
    input_args = method.inputVars;
    from = method.fromAcc;
    method_name = method.name

    if(method_name == 'constructor'){
      if(i > 0){
        constTrace = await debug.getTransactionTrace(constHash, {});
        ans.splice(constpos, 0, constTrace.structLogs);
        returnvals.splice(constpos, 0, "None");
      }
      gas = await contract.deploy({data: bytecode, arguments: input_args}).estimateGas();
      deployed = await contract.deploy({data: bytecode, arguments: input_args}).send({
        from: from,
        gas: gas+1
      }).on('transactionHash', (transactionHash) => {constHash = transactionHash;});
      constpos = i;
    }
    else{
      tx = await eval(`deployed.methods.${method_name}.apply(this, input_args).send({from: from})`);
      txTrace = await debug.getTransactionTrace(tx.transactionHash, {});
      ans.push(txTrace.structLogs);
      returnvals.push(tx.status);
    }
  }
  constTrace = await debug.getTransactionTrace(constHash, {});
  ans.splice(constpos, 0, constTrace.structLogs);
  returnvals.splice(constpos, 0, tx.status);
  return [ans, returnvals];
}

runTest().then(function(arr){
  fs.writeFile("debugs.txt", JSON.stringify(arr[0]), function(err) {
      if(err) {
          return console.log(err);
      }
  });
  fs.writeFile("returnvals.txt", arr[1], function(err) {
      if(err) {
          return console.log(err);
      }
  });
  return arr;
});
