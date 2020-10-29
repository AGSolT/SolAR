import { Network } from 'web3-net';
import * as Utils from 'web3-utils';
import { formatters } from 'web3-core-helpers';
import { ProviderResolver } from 'web3-providers';
import { AbstractMethodFactory, BackTraceAtMethod, BlockProfileMethod, CpuProfileMethod, DumpBlockMethod, GcStatsMethod, GetBlockRlpMethod, GoTraceMethod, MemStatsMethod, SeedHashMethod, SetBlockProfileRateMethod, SetHeadMethod, StacksMethod, StartCpuProfileMethod, StopCpuProfileMethod, StartGoTraceMethod, StopGoTraceMethod, TraceBlockMethod, TraceBlockByNumberMethod, TraceBlockByHashMethod, TraceBlockFromFileMethod, TraceTransactionMethod, VerbosityMethod, VmoduleMethod, WriteBlockProfileMethod, WriteMemProfileMethod } from 'web3-core-method';
import { AbstractWeb3Module } from 'web3-core';

class MethodFactory extends AbstractMethodFactory {
  constructor(utils, formatters) {
    super(utils, formatters);
    this.methods = {
      setBackTraceAt: BackTraceAtMethod,
      blockProfile: BlockProfileMethod,
      cpuProfile: CpuProfileMethod,
      dumpBlock: DumpBlockMethod,
      getGCStats: GcStatsMethod,
      getBlockRlp: GetBlockRlpMethod,
      goTrace: GoTraceMethod,
      getMemStats: MemStatsMethod,
      getSeedHash: SeedHashMethod,
      setBlockProfileRate: SetBlockProfileRateMethod,
      setHead: SetHeadMethod,
      getStacks: StacksMethod,
      startCPUProfile: StartCpuProfileMethod,
      stopCPUProfile: StopCpuProfileMethod,
      startGoTrace: StartGoTraceMethod,
      stopGoTrace: StopGoTraceMethod,
      getBlockTrace: TraceBlockMethod,
      getBlockTraceByNumber: TraceBlockByNumberMethod,
      getBlockTraceByHash: TraceBlockByHashMethod,
      getBlockTraceFromFile: TraceBlockFromFileMethod,
      getTransactionTrace: TraceTransactionMethod,
      setVerbosity: VerbosityMethod,
      setVerbosityPattern: VmoduleMethod,
      writeBlockProfile: WriteBlockProfileMethod,
      writeMemProfile: WriteMemProfileMethod
    };
  }
}

class Debug extends AbstractWeb3Module {
  constructor(provider, methodFactory, net, utils, formatters, options, nodeNet) {
    super(provider, options, methodFactory, nodeNet);
    this.utils = utils;
    this.formatters = formatters;
    this.net = net;
  }
  setProvider(provider, net) {
    return !!(super.setProvider(provider, net) && this.net.setProvider(provider, net));
  }
  set defaultGasPrice(value) {
    super.defaultGasPrice = value;
    this.net.defaultGasPrice = value;
  }
  get defaultGasPrice() {
    return super.defaultGasPrice;
  }
  set defaultGas(value) {
    super.defaultGas = value;
    this.net.defaultGas = value;
  }
  get defaultGas() {
    return super.defaultGas;
  }
  set transactionBlockTimeout(value) {
    super.transactionBlockTimeout = value;
    this.net.transactionBlockTimeout = value;
  }
  get transactionBlockTimeout() {
    return super.transactionBlockTimeout;
  }
  set transactionConfirmationBlocks(value) {
    super.transactionConfirmationBlocks = value;
    this.net.transactionConfirmationBlocks = value;
  }
  get transactionConfirmationBlocks() {
    return super.transactionConfirmationBlocks;
  }
  set transactionPollingTimeout(value) {
    super.transactionPollingTimeout = value;
    this.net.transactionPollingTimeout = value;
  }
  get transactionPollingTimeout() {
    return super.transactionPollingTimeout;
  }
  set defaultAccount(value) {
    super.defaultAccount = value;
    this.net.defaultAccount = value;
  }
  get defaultAccount() {
    return super.defaultAccount;
  }
  set defaultBlock(value) {
    super.defaultBlock = value;
    this.net.defaultBlock = value;
  }
  get defaultBlock() {
    return super.defaultBlock;
  }
}

function Debug$1(provider, net = null, options = {}) {
  const resolvedProvider = new ProviderResolver().resolve(provider, net);
  return new Debug(resolvedProvider, new MethodFactory(Utils, formatters), new Network(resolvedProvider, null, options), Utils, formatters, options, null);
}

export { Debug$1 as Debug };
