from CDG import *
from Test_Suite import *
from Test import *
import ast, random, copy

def generate_offspring(test_cases, SmartContract, accounts, deploying_accounts, poss_methods, pop_size, tournament_size, max_method_calls, crossover_probability, remove_probability, change_probability, insert_probability, _maxWei):
    """
    Given a set of parent test-cases generates offspring by applying selection, crossover and mutation.
    Inputs:
        - test_cases: The set of parent test-cases.
        - accounts: The list of accounts that can interact with deployed smart contracts.
        - poss_methods: A dictionary of all the methods of the smart contract.
        - pop_size: The population size of a test suite
        - tournament_size: The size of the tournament used for selection.
        - max_method_calls: The maximum number of method calls of any test-case.
        - crossover_probability: The probability of crossover occuring (as opposed to cloning the parents.)
    Outputs:
        - Q: A set of population size, consisting of offspring of the parent test-cases.
    """
    Q = set()
    while len(Q)<pop_size:
        parent1 = tournament_selection(test_cases, tournament_size)
        parent2 = tournament_selection(test_cases, tournament_size)
        if random.uniform(0,1)<= crossover_probability:
            child1, child2 = crossover(parent1, parent2, SmartContract, accounts, deploying_accounts, max_method_calls)
        else:
            child1 = copy.deepcopy(parent1)
            child2 = copy.deepcopy(parent2)

        mutate(child1, accounts, poss_methods, max_method_calls, remove_probability, change_probability, insert_probability, _maxWei)
        mutate(child2, accounts, poss_methods, max_method_calls, remove_probability, change_probability, insert_probability, _maxWei)
        if child1 == parent1:
            assert child2==parent2, "child1 is the same as parent1 but child2 is not the same as parent2 during crossover!"
        else:
            Q.add(child1)
            Q.add(child2)
    return Q

def tournament_selection(testCases, tournament_size):
    """
    Holds a tournament and selects a winner as a candidate to generate offspring based on their non-dominated Pareto front and sub-vector distance.
    Inputs:
        - testCases: The set of potential parent test-cases.
        - tournament_size: The number of participating test-cases in the tournament.
    Outputs:
        - winner: The optimal test-case according to non-dominated Pareto front and sub-vector distance.
    """
    participants = random.sample(testCases, tournament_size)
    winner = participants[0]
    for participant in participants[1:]:
        if participant.rank < winner.rank:
            winner = participant
        elif (participant.rank == winner.rank) & (participant.subvector_dist < winner.subvector_dist):
            winner = participant
    return winner

def crossover(testCase1, testCase2, SmartContract, accounts, deploying_accounts, max_method_calls):
    """
    Given two test-cases, produces two chilren by applying single-point crossover.
    Inputs:
        - testCase1, testCase2: The test-cases used to produce offspring.
    Outputs:
        - ans1, ans2: The two children
    """
    alpha = random.uniform(0,1)
    alpha_int = min(int(alpha*len(testCase1.methodCalls)), int(alpha*len(testCase2.methodCalls)))
    ans1_methodcalls = testCase1.methodCalls[:alpha_int] + testCase2.methodCalls[alpha_int:]
    ans2_methodcalls = testCase2.methodCalls[:alpha_int] + testCase1.methodCalls[alpha_int:]

    ans1 = TestCase(ans1_methodcalls, _random = False, SmartContract = SmartContract, accounts = accounts, deploying_accounts = deploying_accounts, max_method_calls = max_method_calls)
    ans2 = TestCase(ans2_methodcalls, _random = False, SmartContract = SmartContract, accounts = accounts, deploying_accounts = deploying_accounts, max_method_calls = max_method_calls)
    return ans1, ans2

# Each mutation type is applied with probability 1/3
def mutate(testCase, accounts, poss_methods, max_method_calls, remove_probability, change_probability, insert_probability, _maxWei, val_dict = {}):
    """
    Mutates a given test case by removing one or more method calls, changing the method calls input value or inserting new method calls.
    Inputs:
        - testCase: The test-case to be mutated.
        - accounts: The accounts used to interact with deployed smart contracts.
        - poss_methods: The methods of the smart contract.
        - max_method_calls: The maximum number of method calls per test-case
        - remove_probability: The probability that the test case is mutated with the remove-mutation.
        - change_probability: The probability that the test case is mutated with the change-mutation.
        - insert_probability: The probability that the test case is mutated with the insert-mutation.
    Outputs:
        - The mutated test-case
    """
    if random.uniform(0,1)<=remove_probability:
        # Remove mutation
        delprob = len(testCase.methodCalls)
        for i, methodCall in enumerate(testCase.methodCalls):
            # Each methodcall is deleted with probability 1/length(testCase.methodCalls)
            if random.uniform(0, delprob)<=1:
                if i == 0:
                    pass # We can not delete the constructor
                else:
                    del testCase.methodCalls[i]
    if random.uniform(0,1)<=change_probability:
        # Change mutation
        for i, methodCall in enumerate(testCase.methodCalls):
            old_inputvars = methodCall.inputvars
            new_inputvars = old_inputvars.copy()
            new_fromAcc = methodCall.fromAcc
            new_value = methodCall.value
            old_value = new_value
            # Each methodcall is changed with probability 1/length(testCase.methodCalls)
            if random.uniform(0, len(testCase.methodCalls))<=1:
                if random.uniform(0,1)<=0.95: # mutate inputvars
                    if len(old_inputvars) == 0:
                        pass
                    else:
                        for j, old_inputvar in enumerate(old_inputvars):
                            if random.uniform(0, len(old_inputvars))<=1:
                                if type(old_inputvar) == bool:
                                    new_inputvar = not old_inputvar
                                elif type(old_inputvar) == int:
                                    delta = random.choice(range(1,11))
                                    if random.uniform(0,1)<=0.5:
                                        new_inputvar = max(0, old_inputvar-delta)
                                    else:
                                        new_inputvar = min(255, old_inputvar+delta)
                                elif type(old_inputvar == str):
                                    if old_inputvar in accounts:
                                        new_inputvar = random.choice(accounts)
                                    else:
                                        new_inputvar = mutate_string(old_inputvar)
                                else:
                                    assert False, "Unknown input variable type: {}".format(old_inputvar)
                                new_inputvars[j] = new_inputvar
                if random.uniform(0,1)<=0.05: # mutate fromAcc
                    new_fromAcc = random.choice(accounts)
                if methodCall.payable:
                    if random.uniform(0,1)<=0.05: # mutate value
                        delta = random.uniform(0, _maxWei)*0.1
                        if random.uniform(0,1)<=0.5:
                            new_value = max(0, old_value-delta)
                        else:
                            new_value = min(_maxWei, old_value+delta)
            # mutate value
            methodName = methodCall.methodName
            new_methodCall = MethodCall(methodName, new_inputvars, new_fromAcc, new_value, methodCall.payable)
            testCase.methodCalls[i] = new_methodCall
    if random.uniform(0,1)<=insert_probability:
        # Insert mutation
        add_new = True
        prop = 0
        while(add_new) & (len(testCase.methodCalls)<max_method_calls):
            try:
                new_methodCall = MethodCall(None, None, None, None, _payable=None, methodDict = random.choice(poss_methods), accounts = accounts)
            except:
                sys.exit(f"couldn't create a new methodCall, I'm guessing there's something wrong with poss_methods: {poss_methods}")
            if len(testCase.methodCalls) == 1:
                loc = 1
            else:
                loc = random.choice(range(1,len(testCase.methodCalls)))
            testCase.methodCalls.insert(loc, new_methodCall)
            prop += 1
            add_new = random.uniform(0,1)<=0.5**prop
    return


def mutate_string(s):
    """
    Takes a string and mutates it by applying remove, change and insert operation
    Inputs:
     - s: the string that needs to be mutated.
    Outputs:
     - s_out: the string after mutation.
    """
    # remove
    if random.uniform(0,1)<=1/3:
        s_out = ""
        del_prob=1/len(s)
        for i in range(len(s)):
            if random.uniform(0,1)>del_prob:
                s_out = s_out+s[i]
    else:
        s_out = s

    # change
    if random.uniform(0,1)<=1/3:
        change_prob = 0.95
        for i in range(len(s_out)):
            if random.uniform(0,1)<=change_prob:
                s_out = s_out[:i] + random.choice(string.ascii_letters+""" """) + s_out[i+1:]

    # insert
    if random.uniform(0,1)<=1/3:
        # Insert mutation
        add_new = True
        prop = 0
        while(add_new) & (len(s_out)<256):
            new_char = random.choice(string.ascii_letters+""" """)
            loc = random.choice(range(0,len(s_out)))
            s_out = s_out[:loc] + new_char + s_out[loc:]
            prop += 1
            add_new = random.uniform(0,1)<=0.5**prop

    return s_out
