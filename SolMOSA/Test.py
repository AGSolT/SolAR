"""
This module contains all code necessary to create and interact with test cases.

Classes:
    - TestCase:     The class describing a test case.
    - MethodCall:   The class describing a method call.
"""

import random
import string
import math
import logging
import re
import numpy as np


class TestCase():
    """
    A testcase consisting of method calls and having properties that describe \
    it's performance.

    Properties:
        - methodCalls:      A list of all the MethodCalls in the TestCase,
                            the first MethodCall is always a constructor.
        - returnVals:       The return values of each of the methodCalls.
        - distance_vector:  The distance vector, giving the distance from the
                            test case to each of the branches.
        - S:                The set of test cases that are dominated by this
                            test case, used during the fast-non-dominated-sort
                            procedure.
        - n:                The domination-count used during the
                            fast-non-dominated-sort procedure.
        - rank:             Indicator that shows to which non-dominated-front
                            this test case belongs.
        - subvector_dist:   The subvector distance, used to compare different
                            test cases in the same non-dominated Pareto-front.
    """

    methodCalls = []
    returnVals = []
    distance_vector = None
    S = []
    n = 0
    rank = math.inf
    subvector_dist = 0

    def __init__(
            self, _methodCalls, _maxArrayLength, _random=False,
            SmartContract=None, accounts=None, deploying_accounts=None,
            _minArrayLength=1, _addresspool=None, _ETHpool=None, _intpool=None,
            _stringpool=None, max_method_calls=None, min_method_calls=0,
            passBlocks=False, passTime=False, passTimeTime=None,
            _zeroAddress=False, _maxWei=10000000000000000000):
        """
        Initialise a test case, either by passing all of it's  properties \
        or initialise randomly by generating a random number of random \
        methodcalls.

        When a testcase is created, it never has distances
        assigned to it or any information about domination.
        """
        if not _random:
            self.methodCalls = _methodCalls
            self.returnVals = []
            self.distance_vector = None
            self.S = []
            self.n = 0
            self.rank = math.inf
            self.subvector_dist = 0
        else:
            poss_methods = SmartContract.methods.copy()
            assert poss_methods[0]['type'] == 'constructor',\
                f"The first method in a SmartContract should always be it's\
                 constructor. Instead it is {poss_methods[0]}"

            if passTime:
                assert passTimeTime is not None, \
                    "a passTime block is trying to be created \
                but no time has been specified!"
                passTimeMethod = {"constant": 'true',
                                  "inputs": [{"name": "", "type": "int256"}],
                                  "name": "passTime", "outputs": [],
                                  "payable": False, "stateMutability": "view",
                                  "type": "passTime"}
                poss_methods = poss_methods + [passTimeMethod]
            if passBlocks:
                passBlocksMethod = {"constant": 'true', "inputs": [],
                                    "name": "passBlocks", "outputs": [],
                                    "payable": False,
                                    "stateMutability": "view",
                                    "type": "passBlocks"}
                poss_methods = poss_methods + [passBlocksMethod]

            methodCalls = [MethodCall(
                _methodName=None, _inputvars=None, _fromAcc=None, _value=None,
                _payable=None, _maxArrayLength=_maxArrayLength,
                methodDict=poss_methods[0], accounts=accounts,
                deploying_accounts=deploying_accounts,
                _minArrayLength=_minArrayLength, _addresspool=_addresspool,
                _ETHpool=_ETHpool, _intpool=_intpool, _stringpool=_stringpool,
                _passTimeTime=passTimeTime, _zeroAddress=_zeroAddress,
                _maxWei=_maxWei)]

            poss_methods.pop(0)
            assert len(poss_methods) > 0, \
                "A contract should have at least one method \
            other than it's constructor."
            nr_of_method_calls = random.randint(
                min_method_calls, max_method_calls)

            for i in range(nr_of_method_calls):
                randMethod = random.choice(poss_methods)
                methodCalls = methodCalls + [MethodCall(
                    _methodName=None, _inputvars=None, _fromAcc=None,
                    _value=None, _payable=None,
                    _maxArrayLength=_maxArrayLength, methodDict=randMethod,
                    accounts=accounts, deploying_accounts=deploying_accounts,
                    _minArrayLength=_minArrayLength, _addresspool=_addresspool,
                    _ETHpool=_ETHpool, _intpool=_intpool,
                    _stringpool=_stringpool, _passTimeTime=passTimeTime,
                    _zeroAddress=_zeroAddress, _maxWei=_maxWei)]

            self.methodCalls = methodCalls
            self.returnVals = []
            self.distance_vector = None
            self.S = []
            self.n = 0
            self.rank = math.inf
            self.subvector_dist = 0

    def show_test(self, log=False):
        """Show all the method calls in the test case."""
        info = """"""
        for i, methodCall in enumerate(self.methodCalls):
            info = info + "\t({}) {}({}, from: {}, value: {})\n".format(
                i + 1, methodCall.methodName, methodCall.inputvars,
                methodCall.fromAcc, methodCall.value)
        if log:
            logging.info(info)
        else:
            print(info)

    def input_dict_strings(self):
        """Generate the string-input for calling \
        the SC_interaction.js script."""
        ans = """"""
        for methodCall in self.methodCalls:
            input_dict_string = """{{name: '{}', inputVars: {}, """\
                """fromAcc: '{}', value: {}}}""".format(
                    methodCall.methodName, self.InputVars_to_String(
                        methodCall.inputvars), methodCall.fromAcc,
                    methodCall.value)
            if len(ans) > 0:
                ans = ans + """, """ + input_dict_string
            else:
                ans = input_dict_string
        return ans

    def InputVars_to_String(self, _inputvars):
        """Translate Booleans from python to javascript."""
        ans = """["""
        for i, iv in enumerate(_inputvars):
            if i > 0 & i < len(_inputvars) - 1:
                ans = ans + ""","""
            if (isinstance(iv, bool)):
                if (iv):
                    ans = ans + """true"""
                else:
                    ans = ans + """false"""
            elif type(iv) == str:
                ans = ans + """'{}'""".format(iv)
            else:
                ans = ans + """{}""".format(iv)
        ans = ans + """]"""
        return ans

    def update_distance(self, methodResults, returnvals, compactNodes,
                        compactEdges, approach_levels):
        """
        Take the results of all MethodCalls in the test case and uses them to \
        set the distance_vector.

        Arguments:
            - methodResults:    The result of the MethodCalls in the test case,
                                containing the state of the stack during
                                execution.
            - compactNodes:     The Nodes of the CDG of the smart contract.
            - compactEdges:     The Edges of the CDG of the smart contract.
            - approach_levels:  The approach levels between all the branches in
                                the smart contract.
        """
        assert(len(self.methodCalls) == len(methodResults)
               ), "There should be equally many methodCalls and methodResults!"
        edgeset = set()
        test_scores = np.empty(len(compactEdges))
        test_scores.fill(math.inf)
        visited = set()

        for methodCall, methodResult in \
                zip(self.methodCalls[1:], methodResults[1:]):
            if methodResult in ["passTime", "passBlocks"]:
                # These are not real method calls.
                pass
            elif methodResult == "Out of Ether":
                # This did not yield a result
                logging.warning("An account ran out of Ether! Check out the "
                                "blockchain log for more info.")
                pass
            else:
                curNode = next((cNode for cNode in
                                compactNodes if
                                cNode.node_id == ("_dispatcher", 1)), None)
                cur_pc = methodResult[0]['pc']
                assert cur_pc == 0, \
                    "This methodcall doesn't start by going \
                    to the dispatcher: {}".format(methodResult)

                i = 0
                node_stack_items = []
                # Keep going until the last basic_block is reached.
                while (curNode.basic_blocks[-1].end.name != "RETURN") & \
                    (curNode.basic_blocks[-1].end.name != "REVERT") & \
                        (curNode.basic_blocks[-1].end.name != "STOP") & \
                        (curNode.basic_blocks[-1].end.name != "INVALID"):
                    start_pc = curNode.basic_blocks[-1].start.pc
                    end_pc = curNode.basic_blocks[-1].end.pc
                    while not ((cur_pc >= start_pc) & (cur_pc <= end_pc)):
                        # Skip ahead to the last basic_block of the
                        # current Node
                        node_stack_items = node_stack_items + [methodResult[i]]
                        i += 1
                        cur_pc = methodResult[i]['pc']

                    while (cur_pc >= start_pc) & (cur_pc <= end_pc):
                        # Go to the first basic_block outside of the
                        # current Node
                        node_stack_items = node_stack_items + [methodResult[i]]
                        i += 1
                        cur_pc = methodResult[i]['pc']

                    for potential_nextNode in compactNodes:
                        # Find the next Node.
                        if (cur_pc >= potential_nextNode.
                                basic_blocks[0].start.pc) & \
                                (cur_pc <=
                                 potential_nextNode.basic_blocks[0].end.pc):
                            nextNode = potential_nextNode
                            break
                    visited = visited.union({curNode})
                    assert curNode != nextNode, \
                        f"The nextNode that was found: {nextNode.node_id} "\
                        f"was the same as the curNode: {curNode.node_id}."

                    for j, cEdge in enumerate(compactEdges):
                        if (cEdge.startNode_id == curNode.node_id):
                            # Look at all the edges that were not neccessarily
                            # traversed.
                            test_scores[j] = min(test_scores[j],
                                                 self.branch_dist(
                                                 nextNode.node_id,
                                                 node_stack_items, cEdge))
                            if (cEdge.endNode_id == nextNode.node_id):
                                edgeset.add(j)
                        if cEdge.endNode_id == nextNode.node_id:
                            if cEdge.startNode_id in [visitedNode.node_id for
                                                      visitedNode in visited]:
                                test_scores[j] = 0
                            if test_scores[j] == 0:
                                # The edge has been traversed
                                edgeset.add(j)
                    curNode = nextNode

        for i, test_score in enumerate(test_scores):
            if test_score == math.inf:
                test_scores[i] = self.approach_level(
                    approach_levels, edgeset, i)

        self.distance_vector = test_scores
        self.returnVals = returnvals

    def branch_dist(self, nextNode_id, stack_items, compactEdge):
        """
        Identify the predicate in the node that controlls the branch and \
        calculate the corrsponding normalised branch distance.

        Arguments:
            - nextNode_id: The node_id of the next Node that is reached during
                        the execution of the MethodCall.
            - stack_items: The state of the stack during the execution of the
                           node preceding the branch.
            - compactEdge: The edge that corresponds to the branch.
        """
        if nextNode_id == compactEdge.endNode_id:
            return 0
        else:
            pred_eval = compactEdge.predicate.eval
            if pred_eval == "NONE":
                # There is no predicate to evalueate
                return 1
            stack = next((stackItem['stack'] for stackItem in stack_items if
                          stackItem['pc'] == compactEdge.predicate.pc), None)
            if stack is None:
                # The required predicate was not reached
                return 1

            s_1 = int(stack[-1], 16)
            if pred_eval == 'ISZERO':
                return self.normalise(np.abs(s_1))
            s_2 = int(stack[-2], 16)
            if pred_eval == 'EQ':
                if s_1 == s_2:  # The other branch is found by s_1 != s_2
                    return 1
                else:
                    return self.normalise(np.abs(s_1 - s_2))
            else:
                assert pred_eval in ['LT', 'GT', 'SLT', 'SGT'], \
                    "Unknown predicate eval: {}".format(pred_eval)
                if s_1 >= s_2:
                    # The other branch is controlled either by LT or SLT
                    return self.normalise(s_1 - s_2)
                else:
                    # The other branche is controlled either by GT or SGT
                    return self.normalise(s_2 - s_1)

    def normalise(self, val):
        """Normalise a value, by dividing it by itself+1."""
        assert val != -1, "Normalising -1 means dividing by 0!"
        return val / (val + 1)

    def approach_level(self, app_lvls, edgeset, cEdge):
        """
        Find the approach level of the test case for those branches that are \
        not reached.

        Arguments:
            - app_lvls: The approach level matrix with the appraoch levels
                        between each branch.
            - edgeset:  A list of indices corresponding to all the edges
                        traversed by the test case.
        """
        app_lvl = math.inf
        for j in edgeset:
            app_lvl = min(app_lvl, app_lvls[j][cEdge])
        if app_lvl == 0:
            print(f"app_lvl: {app_lvl}\nj:{j}\ncEdge: {cEdge}\n\n\
            app_lvls: {app_lvls}")
        assert app_lvl != 0, "An approach level of 0 should never be used."
        return app_lvl


class MethodCall():
    """
    A class describing the methods of a test case that can be called.

    Properties:
        - methodName:   The name of the method in the CDG of the smart
                        contract.
        - inputVars:    The input variables for this method call.
        - fromAcc:      The blockchain account from which the method call
                        should be made.
        - value:        The amount of wei that should be send with the
                        transaction of the method call.
    """

    methodName = ""
    inputvars = []
    fromAcc = ""
    value = 0
    payable = False

    def __init__(self, _methodName, _inputvars, _fromAcc, _value, _payable,
                 _maxArrayLength,
                 methodDict=None, accounts=None, deploying_accounts=None,
                 _minArrayLength=10, _addresspool=None, _ETHpool=None,
                 _intpool=None, _stringpool=None, _passTimeTime=None,
                 _zeroAddress=False, _maxWei=10000000000000000000):
        """Initialise a method call either by passing all of it's \
        properties or randomly by choosing the properties from within the \
        specified allowed values."""
        if methodDict is None:
            self.methodName = _methodName
            self.inputvars = _inputvars
            self.fromAcc = _fromAcc
            self.value = _value
            self.payable = _payable
        else:
            assert accounts is not None, \
                "A random method call is trying to be created \
                but no accounts were passed."
            assert _addresspool is not None, \
                "No addresspool was passed!"
            if methodDict['type'] == 'constructor':
                self.methodName = "constructor"
                if (len(_addresspool) > 0) & (random.uniform(0, 1) < 0.5):
                    # Take an address from the pool.
                    self.fromAcc = random.choice(tuple(_addresspool))
                else:
                    self.fromAcc = random.choice(deploying_accounts)
                inputvars = []
                for input in methodDict['inputs']:
                    inputvars = inputvars + \
                        [self.Random_Inputvar(
                            input['type'], accounts, _maxArrayLength,
                            _addresspool, _ETHpool, _intpool, _stringpool,
                            _zeroAddress, _minArrayLength)]
                self.inputvars = inputvars
            elif methodDict['type'] == 'passTime':
                self.methodName = "passTime"
                self.fromAcc = random.choice(accounts)
                self.inputvars = [_passTimeTime]
            elif methodDict['type'] == 'passBlocks':
                self.methodName = "passBlocks"
                self.fromAcc = random.choice(accounts)
                inputvars = []
                for input in methodDict['inputs']:
                    inputvars = inputvars + \
                        [self.Random_Inputvar(
                            input['type'], accounts, _maxArrayLength,
                            _addresspool, _ETHpool, _intpool, _stringpool,
                            _zeroAddress, _minArrayLength)]
                self.inputvars = inputvars
            else:
                self.methodName = methodDict['name']
                self.fromAcc = random.choice(accounts)
                inputvars = []
                for input in methodDict['inputs']:
                    inputvars = inputvars + \
                        [self.Random_Inputvar(
                            input['type'], accounts, _maxArrayLength,
                            _addresspool, _ETHpool, _intpool, _stringpool,
                            _zeroAddress, _minArrayLength)]
                self.inputvars = inputvars
            if not methodDict['payable']:
                self.value = 0
                self.payable = False
            else:
                if (len(_ETHpool) > 0) & (random.uniform(0, 1) < 0.5):
                    self.value = random.choice(tuple(_ETHpool))
                else:
                    self.value = random.randint(0, _maxWei)
                self.payable = True

    def Random_Inputvar(self, varType, accounts, _maxArrayLength, _addresspool,
                        _ETHpool, _intpool, _stringpool, _zeroAddress,
                        _minArrayLength=1):
        """Generate a random allowed input variable given the the variable's \
        type."""
        maxArrayLength = _maxArrayLength  # TODO: Make this a parameter.
        minArrayLength = _minArrayLength  # TODO: Make this a parameter.
        if varType[-1] == "]":
            # This is an array
            ArrayLength = random.randint(minArrayLength, maxArrayLength)
            ans = []
            for i in range(ArrayLength):
                ans = ans + [self.Random_Inputvar(
                    varType[:-2], accounts, maxArrayLength, _addresspool,
                    _ETHpool, _intpool, _stringpool, minArrayLength,
                    _zeroAddress)]
            return ans

        elif varType == "bool":
            return random.choice([True, False])
        elif varType[:3] == "int":
            intsize = next((int(s) for s in re.findall(r'-?\d+\.?\d*',
                                                       varType)), None)
            if intsize is None:
                intsize = 256
            assert intsize in [8 * i for i in range(1, 33)], \
                "int was followed by something unusual: {}".format(varType)
            if (len(_intpool) > 0) & (random.uniform(0, 1) < 0.5):
                # Return a relevant integer from the pool.
                try:
                    relevantInts = [num for num in _intpool if num in
                                    range(-(2**intsize - 1), 2**intsize - 1)]
                    return random.choice(relevantInts)
                except:
                    return random.randint(-(2**intsize - 1), 2**intsize - 1)
            else:
                return random.randint(-(2**intsize - 1), 2**intsize - 1)
        elif varType[:4] == "uint":
            intsize = next((int(s) for s in re.findall(r'-?\d+\.?\d*',
                                                       varType)), None)
            if intsize is None:
                intsize = 256
            assert intsize in [
                8 * i for i in range(1, 33)], \
                "int was followed by something unusual: {}".format(varType)
            if (len(_intpool) > 0) & (random.uniform(0, 1) < 0.5):
                # Return a relevant integer from the pool.
                try:
                    relevantInts = [num for num in _intpool if num in
                                    range(0, 2**intsize - 1)]
                    return random.choice(relevantInts)
                except:
                    # The integers from the pool do not fit in the range
                    return random.randint(0, 2**intsize - 1)
            else:
                return random.randint(0, 2**intsize - 1)
        elif varType == "address":
            if (_zeroAddress) & (random.uniform(0, 1) < 0.05):
                return "0x0000000000000000000000000000000000000000"
            if (len(_addresspool) > 0) & (random.uniform(0, 1) < 0.5):
                # Return an address from the pool.
                return random.choice(tuple(_addresspool))
            else:
                return random.choice(accounts)
        elif varType == "string":
            if (len(_stringpool) > 0) & (random.uniform(0, 1) < 0.5):
                # Retrun a string from the pool.
                return random.choice(tuple(_stringpool))
            else:
                string_length = random.randint(1, 255)
                str = ''.join(random.choice(string.ascii_letters + """ """)
                              for x in range(string_length))
                ans = random.choices(["Standard String", str],
                                     weights=[0.1, 0.9], k=1)[0]
                return ans
        else:
            assert False, \
                "This method has an unsupported type: {}".format(varType)
            return 0
