(function (global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined' ? factory(exports, require('web3-net'), require('web3-utils'), require('web3-core-helpers'), require('web3-providers'), require('@babel/runtime/helpers/classCallCheck'), require('@babel/runtime/helpers/possibleConstructorReturn'), require('@babel/runtime/helpers/getPrototypeOf'), require('@babel/runtime/helpers/inherits'), require('web3-core-method'), require('@babel/runtime/helpers/createClass'), require('@babel/runtime/helpers/set'), require('@babel/runtime/helpers/get'), require('web3-core')) :
    typeof define === 'function' && define.amd ? define(['exports', 'web3-net', 'web3-utils', 'web3-core-helpers', 'web3-providers', '@babel/runtime/helpers/classCallCheck', '@babel/runtime/helpers/possibleConstructorReturn', '@babel/runtime/helpers/getPrototypeOf', '@babel/runtime/helpers/inherits', 'web3-core-method', '@babel/runtime/helpers/createClass', '@babel/runtime/helpers/set', '@babel/runtime/helpers/get', 'web3-core'], factory) :
    (global = global || self, factory(global.Web3EthDebug = {}, global.web3Net, global.Utils, global.web3CoreHelpers, global.web3Providers, global._classCallCheck, global._possibleConstructorReturn, global._getPrototypeOf, global._inherits, global.web3CoreMethod, global._createClass, global._set, global._get, global.web3Core));
}(this, function (exports, web3Net, Utils, web3CoreHelpers, web3Providers, _classCallCheck, _possibleConstructorReturn, _getPrototypeOf, _inherits, web3CoreMethod, _createClass, _set, _get, web3Core) { 'use strict';

    _classCallCheck = _classCallCheck && _classCallCheck.hasOwnProperty('default') ? _classCallCheck['default'] : _classCallCheck;
    _possibleConstructorReturn = _possibleConstructorReturn && _possibleConstructorReturn.hasOwnProperty('default') ? _possibleConstructorReturn['default'] : _possibleConstructorReturn;
    _getPrototypeOf = _getPrototypeOf && _getPrototypeOf.hasOwnProperty('default') ? _getPrototypeOf['default'] : _getPrototypeOf;
    _inherits = _inherits && _inherits.hasOwnProperty('default') ? _inherits['default'] : _inherits;
    _createClass = _createClass && _createClass.hasOwnProperty('default') ? _createClass['default'] : _createClass;
    _set = _set && _set.hasOwnProperty('default') ? _set['default'] : _set;
    _get = _get && _get.hasOwnProperty('default') ? _get['default'] : _get;

    var MethodFactory =
    function (_AbstractMethodFactor) {
      _inherits(MethodFactory, _AbstractMethodFactor);
      function MethodFactory(utils, formatters) {
        var _this;
        _classCallCheck(this, MethodFactory);
        _this = _possibleConstructorReturn(this, _getPrototypeOf(MethodFactory).call(this, utils, formatters));
        _this.methods = {
          setBackTraceAt: web3CoreMethod.BackTraceAtMethod,
          blockProfile: web3CoreMethod.BlockProfileMethod,
          cpuProfile: web3CoreMethod.CpuProfileMethod,
          dumpBlock: web3CoreMethod.DumpBlockMethod,
          getGCStats: web3CoreMethod.GcStatsMethod,
          getBlockRlp: web3CoreMethod.GetBlockRlpMethod,
          goTrace: web3CoreMethod.GoTraceMethod,
          getMemStats: web3CoreMethod.MemStatsMethod,
          getSeedHash: web3CoreMethod.SeedHashMethod,
          setBlockProfileRate: web3CoreMethod.SetBlockProfileRateMethod,
          setHead: web3CoreMethod.SetHeadMethod,
          getStacks: web3CoreMethod.StacksMethod,
          startCPUProfile: web3CoreMethod.StartCpuProfileMethod,
          stopCPUProfile: web3CoreMethod.StopCpuProfileMethod,
          startGoTrace: web3CoreMethod.StartGoTraceMethod,
          stopGoTrace: web3CoreMethod.StopGoTraceMethod,
          getBlockTrace: web3CoreMethod.TraceBlockMethod,
          getBlockTraceByNumber: web3CoreMethod.TraceBlockByNumberMethod,
          getBlockTraceByHash: web3CoreMethod.TraceBlockByHashMethod,
          getBlockTraceFromFile: web3CoreMethod.TraceBlockFromFileMethod,
          getTransactionTrace: web3CoreMethod.TraceTransactionMethod,
          setVerbosity: web3CoreMethod.VerbosityMethod,
          setVerbosityPattern: web3CoreMethod.VmoduleMethod,
          writeBlockProfile: web3CoreMethod.WriteBlockProfileMethod,
          writeMemProfile: web3CoreMethod.WriteMemProfileMethod
        };
        return _this;
      }
      return MethodFactory;
    }(web3CoreMethod.AbstractMethodFactory);

    var Debug =
    function (_AbstractWeb3Module) {
      _inherits(Debug, _AbstractWeb3Module);
      function Debug(provider, methodFactory, net, utils, formatters, options, nodeNet) {
        var _this;
        _classCallCheck(this, Debug);
        _this = _possibleConstructorReturn(this, _getPrototypeOf(Debug).call(this, provider, options, methodFactory, nodeNet));
        _this.utils = utils;
        _this.formatters = formatters;
        _this.net = net;
        return _this;
      }
      _createClass(Debug, [{
        key: "setProvider",
        value: function setProvider(provider, net) {
          return !!(_get(_getPrototypeOf(Debug.prototype), "setProvider", this).call(this, provider, net) && this.net.setProvider(provider, net));
        }
      }, {
        key: "defaultGasPrice",
        set: function set(value) {
          _set(_getPrototypeOf(Debug.prototype), "defaultGasPrice", value, this, true);
          this.net.defaultGasPrice = value;
        }
        ,
        get: function get() {
          return _get(_getPrototypeOf(Debug.prototype), "defaultGasPrice", this);
        }
      }, {
        key: "defaultGas",
        set: function set(value) {
          _set(_getPrototypeOf(Debug.prototype), "defaultGas", value, this, true);
          this.net.defaultGas = value;
        }
        ,
        get: function get() {
          return _get(_getPrototypeOf(Debug.prototype), "defaultGas", this);
        }
      }, {
        key: "transactionBlockTimeout",
        set: function set(value) {
          _set(_getPrototypeOf(Debug.prototype), "transactionBlockTimeout", value, this, true);
          this.net.transactionBlockTimeout = value;
        }
        ,
        get: function get() {
          return _get(_getPrototypeOf(Debug.prototype), "transactionBlockTimeout", this);
        }
      }, {
        key: "transactionConfirmationBlocks",
        set: function set(value) {
          _set(_getPrototypeOf(Debug.prototype), "transactionConfirmationBlocks", value, this, true);
          this.net.transactionConfirmationBlocks = value;
        }
        ,
        get: function get() {
          return _get(_getPrototypeOf(Debug.prototype), "transactionConfirmationBlocks", this);
        }
      }, {
        key: "transactionPollingTimeout",
        set: function set(value) {
          _set(_getPrototypeOf(Debug.prototype), "transactionPollingTimeout", value, this, true);
          this.net.transactionPollingTimeout = value;
        }
        ,
        get: function get() {
          return _get(_getPrototypeOf(Debug.prototype), "transactionPollingTimeout", this);
        }
      }, {
        key: "defaultAccount",
        set: function set(value) {
          _set(_getPrototypeOf(Debug.prototype), "defaultAccount", value, this, true);
          this.net.defaultAccount = value;
        }
        ,
        get: function get() {
          return _get(_getPrototypeOf(Debug.prototype), "defaultAccount", this);
        }
      }, {
        key: "defaultBlock",
        set: function set(value) {
          _set(_getPrototypeOf(Debug.prototype), "defaultBlock", value, this, true);
          this.net.defaultBlock = value;
        }
        ,
        get: function get() {
          return _get(_getPrototypeOf(Debug.prototype), "defaultBlock", this);
        }
      }]);
      return Debug;
    }(web3Core.AbstractWeb3Module);

    function Debug$1(provider) {
      var net = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : null;
      var options = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : {};
      var resolvedProvider = new web3Providers.ProviderResolver().resolve(provider, net);
      return new Debug(resolvedProvider, new MethodFactory(Utils, web3CoreHelpers.formatters), new web3Net.Network(resolvedProvider, null, options), Utils, web3CoreHelpers.formatters, options, null);
    }

    exports.Debug = Debug$1;

    Object.defineProperty(exports, '__esModule', { value: true });

}));
