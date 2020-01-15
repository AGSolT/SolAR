// This script connects to the Ethereum simulator that is listening at the specified port and deploys the contract and calls it's methods following the --methods argument.
const Web3 = require('web3')
const fs = require('fs');
const Debug = require('web3-eth-debug').Debug;
const args = require('minimist')(process.argv.slice(2));
const assert = require('assert');
const options = {
    transactionConfirmationBlocks: 1,
}

var data = fs.readFileSync('tests.txt', 'utf8');
const methods = eval(data);
const port = args.ETH_port;
const web3 = new Web3(new Web3.providers.HttpProvider(port), null, options);
const debug = new Debug(new Web3.providers.HttpProvider(port), null, options);

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
  var last_TxTrace = 0;

  for (var i = 0; i < methods.length; i++){
    last_block = await web3.eth.getBlock("latest");
    method = methods[i];
    input_args = method.inputVars;
    from = method.fromAcc;
    method_name = method.name
    console.log(`calling ${method_name}${input_args} from ${from}`)
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
    else if (method_name.substring(0,8) == 'passTime') {
      console.log("I'm really gonna do it!");
      web3.currentProvider.send({method: "evm_increaseTime", params: input_args},function(err, result){});
      ans.push(method_name);
      returnvals.push(method_name);
      continue;
    }
    else if (method_name.substring(0,10) == 'passBlocks') {
      web3.currentProvider.send({jsonrpc: "2.0", method: "evm_mine", params: [], id: 0}, function(err, result){});
      ans.push(method_name);
      returnvals.push(method_name);
      continue;
    }
    else{
      try{
        // See if the transaction executes without returning an error
        tx = await eval(`deployed.methods.${method_name}.apply(this, input_args).send({from: from})`);
      }
      catch(err){
        // Revert errors are good and should still be processed!
        if(err.toString().search("revert")==-1&&err.toString().search('Invalid JSON RPC response: ""')==-1){
          throw `encountered an error which is not revert: ${err}`
        }
        else{
          new_last_block = await web3.eth.getBlock("latest");
          max_iterations = 10;
          iteration=0;
          while(new_last_block.number==last_block.number&&iteration<max_iterations){
            console.log(`Waiting for block to be processed, trying ${max_iterations-iteration-1} more times.`)
            new_last_block = await web3.eth.getBlock("latest");
            iteration+=1;
          }
          last_block = new_last_block;
          tx = new_last_block.transactions[new_last_block.transactions.length-1];
        }
      }
      if(typeof(tx)=='string'){
        txTrace = await debug.getTransactionTrace(tx, {});
      }
      else{
        txTrace = await debug.getTransactionTrace(tx.transactionHash, {});
      }

      assert(last_TxTrace!=txTrace);
      last_TxTrace=txTrace;
      ans.push(txTrace.structLogs);
      returnvals.push(tx.status);
    }
    // REMOVE THIS
    if (method_name.substring(0,7) == 'TestOne') {
      break;
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
