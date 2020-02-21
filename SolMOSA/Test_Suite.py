"""The test Suite module keeps track of each generation of sets of test \
cases."""

# import os
# import configparser
import pickle
# import ast
import logging
from Test import TestCase


class TestSuite():
    """
    A TestSuite object that is used to keep track of all the tests that are \
    currently in a test suite.

    Properties:
        - smartContract: A SmartContract object.
        - tests: A list of tests.
        - accounts: All the accounts that can possibly deploy or interact \
        with smart contracts on the blockchain.
    """

    smartContract = None
    tests = []
    accounts = []
    addresspool = None
    ETHpool = None
    intpool = None
    stringpool = None

    def __init__(self, _SmartContract, _accounts, _deploying_accounts,
                 _addresspool, _ETHpool, _intpool, _stringpool,
                 _pop_size=50, _random=True, _tests=[], _max_method_calls=10,
                 _min_method_calls=0, _passBlocks=False, _passTime=False,
                 _passTimeTime=None, _zeroAddress=False,
                 _maxWei=10000000000000000000):
        """Initialise a Test Suite either randomlhy, or by \
        passing all of it's properties explicitly."""
        if not _random:
            self.smartContract = _SmartContract
            self.tests = _tests
            self.accounts = _accounts
            self.addresspool = _addresspool
            self.ETHpool = _ETHpool
            self.intpool = _intpool
            self.stringpool = _stringpool
        else:
            if(len(_tests) > 0):
                logging.warning("You created a random test suite but also \
                passed some tests as an argument, did you mean to set _random \
                to false?")
            self.smartContract = _SmartContract
            self.accounts = _accounts
            self.addresspool = _addresspool
            self.ETHpool = _ETHpool
            self.intpool = _intpool
            self.stringpool = _stringpool
            tests = []
            for i in range(_pop_size):
                tests = tests + \
                    [TestCase(_methodCalls=None, _random=True,
                              SmartContract=_SmartContract, accounts=_accounts,
                              deploying_accounts=_deploying_accounts,
                              _addresspool=_addresspool, _ETHpool=_ETHpool,
                              _intpool=_intpool, _stringpool=_stringpool,
                              max_method_calls=_max_method_calls,
                              min_method_calls=_min_method_calls,
                              passBlocks=_passBlocks, passTime=_passTime,
                              passTimeTime=_passTimeTime,
                              _zeroAddress=_zeroAddress, _maxWei=_maxWei)]
            self.tests = tests

    def show_tests(self, _top_n=None, log=False):
        """Show all tests in the test suite."""
        if log:
            logging.info("Showing test-suite for {}:".format(
                self.smartContract.contractName))
            if _top_n is None:
                for i, test in enumerate(self.tests):
                    logging.info("test: {}".format(i))
                    test.show_test(log=True)
            else:
                assert _top_n <= len(self.tests), \
                    "The number of tests that can be shown cannot exceed \
                    the total number of tests!"
                for i, test in enumerate(self.tests[:_top_n]):
                    logging.info("test: {}".format(i + 1))
                    test.show_test(log=True)
        else:
            print("Showing test-suite for {}:".format(
                self.smartContract.contractName))
            if _top_n is None:
                for i, test in enumerate(self.tests):
                    print("test: {}".format(i))
                    test.show_test()
            else:
                assert _top_n <= len(self.tests), \
                    "The number of tests that can be shown cannot exceed the \
                    total number of tests!"
                for i, test in enumerate(self.tests[:_top_n]):
                    print("test: {}".format(i + 1))
                    test.show_test()

    def generate_test_inputs(self):
        """Create a string that can be used by SC_interaction.js script to \
        deploy and interact with smart contracts."""
        ans = """"""
        for test in self.tests:
            test_inputs = test.input_dict_strings()
            if len(ans) > 0:
                ans = ans + """, """ + test_inputs
            else:
                ans = test_inputs
        return "[" + ans + "]"

    def update_test_distances(self, callResults, returnvals):
        """Calculate the branch distance vector for each test in self.tests.

        Inputs:
            - callResults: A description of the evaluation of a methodcall or \
            smart contract deployment.
        Result:
            - Each test in the TestSuite has an updated branch distance vector.
        """
        start = 0
        end = 0
        cNodes = self.smartContract.CDG.CompactNodes
        cEdges = self.smartContract.CDG.CompactEdges
        app_lvls = self.smartContract.approach_levels

        for testCase in self.tests:
            end = end + len(testCase.methodCalls)
            methodResults = callResults[start:end]
            rVals = returnvals[start:end]
            testCase.update_distance(
                methodResults, rVals, cNodes, cEdges, app_lvls)
            start = end

    def save_TestSuite(self, save_location):
        """
        Save the current state of the TestSuite as a pickle object.

        Inputs:
            - save_location: The location where the pickle object will be
                             saved.
        """
        with open(save_location, "wb") as f:
            pickle.dump(self, f)
