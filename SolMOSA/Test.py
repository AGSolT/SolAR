import json, random, string, math, logging
import numpy as np
from CDG import *

class TestCase():
    """
    A testcase consisting of method calls and having properties that describe it's performance.
    Properties:
        - methodCalls: A list of all the MethodCalls in the TestCase, the first MethodCall is always a constructor.
        - distance_vector: The distance vector, giving the distance from the test case to each of the branches.
        - S: The set of test cases that are dominated by this test case, used during the fast-non-dominated-sort procedure. #TODO: See if this should be reworked.
        - The domination-count used during the fast-non-dominated-sort procedure.
        - rank: Indicator that shows to which non-dominated-front this test case belongs.
    """
    methodCalls = []
    returnVals = []
    distance_vector = None
    S = []
    n = 0
    rank = math.inf
    subvector_dist = 0

    def __init__(self, _methodCalls, _random=False, SmartContract=None, accounts=None, deploying_accounts = None, max_method_calls=None, min_method_calls=0):
        """
        A test case can either be created by passing all of it's properties or initialised randomly by generating a randmo number of random methodcalls. When a testcase is created, it never has distances assigned to it or any information about domination. TODO: argue why the constructor should allways be the first account or not.
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
            assert poss_methods[0]['type'] == 'constructor', "The first method in a SmartContract should always be it's contructor."
            methodCalls = [MethodCall(_methodName = None, _inputvars = None, _fromAcc = None, _value = None, methodDict = poss_methods[0], accounts = accounts, deploying_accounts = deploying_accounts)]
            poss_methods.pop(0)
            assert len(poss_methods)>0, "A contract should have at least one method other than it's constructor."
            nr_of_method_calls = random.randint(min_method_calls, max_method_calls)

            for i in range(nr_of_method_calls):
                randMethod = random.choice(poss_methods)
                methodCalls = methodCalls + [MethodCall(_methodName = None, _inputvars = None, _fromAcc = None, _value = None, methodDict = randMethod, accounts = accounts, deploying_accounts = deploying_accounts)]

            self.methodCalls = methodCalls
            self.returnVals = []
            self.distance_vector = None
            self.S = []
            self.n = 0
            self.rank = math.inf
            self.subvector_dist = 0

    def show_test(self, log=False):
        """
        Shows all the method calls in the test case.
        """
        info = """"""
        for i, methodCall in enumerate(self.methodCalls):
            info = info + "\t({}) {}({}, from: {}, value: {}\n)".format(i+1, methodCall.methodName, methodCall.inputvars, methodCall.fromAcc, methodCall.value)
        if log:
            logging.info(info)
        else:
            print(info)

    def input_dict_strings(self):
        """
        Generates the string-input necessary to call the SC_interaction.js script.
        """
        ans = """"""
        for methodCall in self.methodCalls:
            input_dict_string = """{{name: '{}', inputVars: {}, fromAcc: '{}', value: {}}}""".format(methodCall.methodName, methodCall.inputvars, methodCall.fromAcc, methodCall.value)
            if len(ans)>0:
                ans = ans + """, """ + input_dict_string
            else:
                ans = input_dict_string
        return ans

    def update_distance(self, methodResults, returnvals, compactNodes, compactEdges, approach_levels):
        """
        Takes the result of all MethodCalls in this test case and uses them to set the distance_vector.
        Inputs:
            - methodResults: The result of the MethodCalls in the test case, containing the state of the stack during execution.
            - compactNodes: The Nodes of the CDG of the smart contract.
            - compactEdges: The Edges of the CDG of the smart contract.
            - approach_levels: The approach levels between all the branches in the smart contract.
        """
        assert(len(self.methodCalls) == len(methodResults)), "There should be equally many methodCalls and methodResults!"
        edgeset = set()
        test_scores = np.empty(len(compactEdges))
        test_scores.fill(math.inf)
        visited = set()

        for methodCall, methodResult in zip(self.methodCalls[1:], methodResults[1:]):
            curNode = next((cNode for cNode in compactNodes if cNode.node_id == ("_dispatcher", 1)), None)
            cur_pc = methodResult[0]['pc']
            assert cur_pc == 0, "This methodcall doesn't start by going to the dispatcher: {}".format(methodResult)

            i = 0
            node_stack_items = []

            while curNode.basic_blocks[-1].end.name!="RETURN":
                start_pc = curNode.basic_blocks[-1].start.pc
                end_pc = curNode.basic_blocks[-1].end.pc
                while not ((cur_pc>=start_pc) & (cur_pc <= end_pc)):
                    node_stack_items = node_stack_items + [methodResult[i]]
                    i += 1
                    cur_pc = methodResult[i]['pc']
                while (cur_pc>=start_pc) & (cur_pc <= end_pc):
                    node_stack_items = node_stack_items + [methodResult[i]]
                    i += 1
                    cur_pc = methodResult[i]['pc']

                for potential_nextNode in compactNodes:
                    if (cur_pc>=potential_nextNode.basic_blocks[0].start.pc) & (cur_pc <= potential_nextNode.basic_blocks[0].end.pc):
                        nextNode = potential_nextNode
                        break
                visited = visited.union({curNode})

                for j, cEdge in enumerate(compactEdges):
                    if (cEdge.startNode_id == curNode.node_id):
                        # print("methodCall: {}".format(methodCall.methodName))
                        # print("input: {}".format(methodCall.inputvars))
                        # print("edge: {}".format(j))
                        # print("branch_dist: {}".format(self.branch_dist(nextNode.node_id, node_stack_items, cEdge)))
                        test_scores[j] = min(test_scores[j], self.branch_dist(nextNode.node_id, node_stack_items, cEdge))
                        # print("test_score: {}".format(test_scores[j]))
                        if (cEdge.endNode_id == nextNode.node_id):
                            edgeset.add(j)
                    if cEdge.endNode_id == nextNode.node_id:
                        if cEdge.startNode_id in [visitedNode.node_id for visitedNode in visited]:
                            test_scores[j] = 0
                            edgeset.add(j)
                curNode = nextNode

        for i, test_score in enumerate(test_scores):
            if test_score == math.inf:
                test_scores[i] = self.approach_level(approach_levels, edgeset, i)

        self.distance_vector = test_scores
        self.returnVals = returnvals

    def branch_dist(self, nextNode_id, stack_items, compactEdge):
        """
        Identifies the predicate in the node that controlls the branch and calculates the corrsponding normalised branch distance.
        Inputs:
            - nextNode_id: The node_id of the next Node that is reached during the execution of the MethodCall.
            - stack_items: The state of the stack during the execution of the node preceding the branch.
            - compactEdge: The edge that corresponds to the branch.
        """
        predicates = ['LT', 'GT', 'SLT', 'SGT', 'EQ', 'ISZERO', 'NONE']
        if nextNode_id == compactEdge.endNode_id:
            return 0
        else:
            pred_eval = compactEdge.predicate.eval
            assert pred_eval != "NONE", "If a predicate is NONE the branch distance should always be 0!"
            stack = next((stackItem['stack'] for stackItem in stack_items if stackItem['pc'] == compactEdge.predicate.pc), None)
            if stack is None:
                stack = next((stackItem['stack'] for stackItem in stack_items if stackItem['op'] == compactEdge.predicate.eval))
            assert not stack is None, "There was a missing stackitem!"
            s_1 = int(stack[-1], 16)
            if pred_eval == 'ISZERO':
                return self.normalise(np.abs(s_1))
            s_2 = int(stack[-2], 16)
            if pred_eval == 'EQ':
                if s_1 == s_2: # The other branch is found by s_1 != s_2
                    return 1
                else:
                    return self.normalise(np.abs(s_1-s_2))
            else:
                assert pred_eval in ['LT', 'GT', 'SLT', 'SGT'], "Unknown predicate eval: {}".format(pred_id)
                if s_1 >= s_2: # The other branch is controlled either by LT or SLT
                    return self.normalise(s_1-s_2)
                else: # The other branche is controlled either by GT or SGT
                    return self.normalise(s_2-s_1)

    def normalise(self, val):
        """
        Normalises a value, by dividing it by itself+1.
        """
        assert val != -1, "Normalising -1 means dividing by 0!"
        return val/(val+1)

    def approach_level(self, app_lvls, edgeset, cEdge):
        """
        Finds the approach level of the test case for those branches that are not reached.
        Inputs:
            - app_lvls: The approach level matrix with the appraoch levels between each branch.
            - edgeset: A list of indices corresponding to all the edges traversed by the test case.
        """
        app_lvl = math.inf
        for j in edgeset:
            app_lvl = min(app_lvl, app_lvls[j][cEdge])
        assert app_lvl != 0, "An approach level of 0 should never be used."
        return app_lvl

    # def update_front(self, _S, _n):
    #     """
    #     TODO: Remove this function
    #     """
    #     self.S = _S
    #     self.n = _n

class MethodCall():
    """
    A class describing the methods of a test case that can be called.
    Properties:
        - methodName: The name of the method in the CDG of the smart contract.
        - inputVars: The input variables for this method call.
        - fromAcc: The blockchain account from which the method call should be made.
        - value: The amount of wei that should be send with the transaction of the method call.
    """
    methodName = ""
    inputvars = []
    fromAcc = ""
    value = 0

    def __init__(self, _methodName, _inputvars, _fromAcc, _value, methodDict=None, accounts = None, deploying_accounts = None):
        """
        A MethodCall can either be initialised by passing all of it's properties or randomly by choosing the properties from within the specified allowed values.
        """
        if methodDict is None:
            self.methodName = _methodName
            self.inputvars = _inputvars
            self.fromAcc = _fromAcc
            self.value = _value
        else:
            assert accounts is not None, "A random method call is trying to be created but no accounts were passed."
            if methodDict['type'] == 'constructor':
                self.methodName = "constructor"
                self.fromAcc = random.choice(deploying_accounts)
            else:
                self.methodName = methodDict['name']
                self.fromAcc = random.choice(accounts)
            if methodDict['payable'] == False:
                self.value = 0
            else:
                self.value = randint(0, 1000000000000000000000)
            inputvars = []
            for input in methodDict['inputs']:
                inputvars = inputvars + [self.Random_Inputvar(input['type'], accounts)]
            self.inputvars = inputvars

    def Random_Inputvar(self, varType, accounts):
        """
        Generates a random allowed input variable given the the variable's type. TODO: Expand the allowed variable types.
        """
        if varType == "bool":
            return random.choice(True, False)
        elif varType[:3] == "int":
            intsize = next((int(s) for s in re.findall(r'-?\d+\.?\d*', varType)), None)
            assert intsize in [8*i for i in range(1, 33)], "int was followed by something unusual: {}".format(varType)
            return random.randint(-(2**intsize-1), 2**intsize-1)
        elif varType[:4] == "uint":
            intsize = next((int(s) for s in re.findall(r'-?\d+\.?\d*', varType)), None)
            assert intsize in [8*i for i in range(1, 33)], "int was followed by something unusual: {}".format(varType)
            # TODO: Large integers return problems for now, maybe these should be passed as strings or bignumbers in javascript?
            return random.randint(0,2**8-1)
            return random.randint(0,2**intsize-1)
        elif varType == "address":
            return random.choice(accounts)
        elif varType == "string":
            string_length = random.randint(1,255)
            str = ''.join(random.choice(string.ascii_letters+"""\ \n\'\"\b\f\r\t\v""") for x in range(string_length))
            return np.random.choice(["Standard String", str], 1, [0.1, 0.9])[0]
        else:
            assert False, "This method has an unsupported type: {}".format(varType)
            return 0

    # bool, int8-int256, uint8-uint256, address/address_payable, Contract: Should be excluded , fixed_bytarrays?, dynamic_bytearrays?, string, rational/integer literal? Enums/Types: should be exluded. Function Types should also be excluded
