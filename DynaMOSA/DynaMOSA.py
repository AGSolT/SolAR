from CDG import *
from SmartContract import *
from Test_Suite import *
from Preference_Sorting import *
from Generate_Offspring import *
import json, pickle, configparser, os, json, ast, subprocess, sys, datetime, time

def DynaMOSA(config):
    """
    The python implementation of DynaMOSA that works on compiled Solidity smart contratcts.
    Prerequisites:
        - An Ethereum blockchain simulator should be running.
        - All the settings need to be specified in a config file
    Inputs:
        - config_file_location: The location of a config_file that specifies all the parameters necessary for the DynaMOSA algorithm.
    Outputs:
        - archives: A list containing the best test cases for each branch at each generation of the algorithm, the final archive in the list contains the best test cases found by the algorithm.
        - tSuite: The TestSuite object that was used by the DynaMOSA algorithm.
        - runtime: The time it took to generate the tests.
        - iterations: The number of times the genetic loop was executed.
    """
    # Register the time when the algorithm starts
    start_time = datetime.datetime.now()

    # config = configparser.ConfigParser()
    # config.read("Config.ini")
    dir_path = os.path.dirname(os.path.realpath(__file__))
    ETH_port = config['Blockchain']['ETH_port']
    max_accounts = int(config['Parameters']['max_accounts'])
    accounts_file_location = dir_path + "/" + config['Files']['accounts_file_location']
    contract_json_location = config['Files']['contract_json_location']
    predicates = config['CFG']['Predicates']
    population_size = int(config['Parameters']['population_size'])
    max_method_calls = int(config['Parameters']['max_method_calls'])
    min_method_calls = int(config['Parameters']['min_method_calls'])
    crossover_probability = float(config['Parameters']['crossover_probability'])
    mutation_probability = float(config['Parameters']['mutation_probability'])
    remove_probability = float(config['Parameters']['remove_probability'])
    change_probability = float(config['Parameters']['change_probability'])
    insert_probability = float(config['Parameters']['insert_probability'])
    search_budget = int(config['Parameters']['search_budget'])
    tournament_size = int(config['Parameters']['tournament_size'])

    accounts, contract_json, contract_name, deployed_bytecode, bytecode, abi = get_ETH_properties(ETH_port, max_accounts, accounts_file_location, contract_json_location)
    if eval(config['Parameters']['deploying_accounts']) == []:
        deploying_accounts = accounts
    else:
        deploying_accounts = eval(config['Parameters']['deploying_accounts'])

    cdg = CDG(contract_name, deployed_bytecode, predicates)

    sc = SmartContract(contract_json, cdg)

    tSuite = TestSuite(sc, accounts, deploying_accounts, _pop_size = population_size, _random = True, _tests = [], _max_method_calls = max_method_calls, _min_method_calls = min_method_calls)
    print("Smart Contract Under investigation: {}".format(contract_json_location))
    relevant_targets = determine_relevant_targets(cdg.CompactEdges, cdg.CompactNodes)
    if sum(relevant_targets) == 0:
        print("No branching paths were detected!")
        return [], tSuite, 0, 0

    callstring = "node SC_interaction.js --methods".split() + [tSuite.generate_test_inputs()] + ["--abi"] + [abi] + ["--bytecode"] + [bytecode] + ["--ETH_port"] + [ETH_port]

    print("Deploying and calling smart contracts for the first time...")
    subprocess.call(callstring)

    with open('debugs.txt', 'r') as f:
        callResults = f.read()

    with open('returnvals.txt', 'r') as f:
        returnvals = f.read().split(",")

    results = ast.literal_eval(callResults)

    print("Updating test distances...")
    tSuite.update_test_distances(results, returnvals)

    init_archive = [None] * len(tSuite.smartContract.CDG.CompactEdges)
    parents = set(tSuite.tests)

    relevant_targets = determine_relevant_targets(tSuite.smartContract.CDG.CompactEdges, tSuite.smartContract.CDG.CompactNodes)

    archive = update_archive(parents, init_archive, relevant_targets)
    archives = [archive]
    testSuites = [tSuite]
    updated_targets = update_targets(parents, archive, relevant_targets)

    Fs = preference_sorting(parents, updated_targets, population_size)

    for F in Fs:
        subvector_dist(F, updated_targets)

    poss_methods = tSuite.smartContract.methods[1:]

    print("{} out of {} branches have been covered".format(len([test for test, relevant in zip(archive, relevant_targets) if (test is not None) & (relevant)]), len([test for test, relevant in zip(archive, relevant_targets) if relevant])))
    print("The following test cases have been are currently in the Archive:")
    for best_test in [best_test for best_test, relevant in zip(archive, relevant_targets) if relevant]:
        if best_test is not None:
            best_test.show_test()
            print("")

    # Keep track of the number of iterations necessary to achieve branch coverage
    iterations = 1

    for i in range(search_budget):
        # Cancel if branch coverage has already been achieved
        if not None in [test for test, relevant in zip(archive, relevant_targets) if relevant]:
            break
        print("Entering main loop iteration {}/{} at {}".format(i+2, search_budget ,datetime.datetime.now().time()))

        print("\tGenerating Offspring...")
        offspring = generate_offspring(parents, sc, accounts, deploying_accounts, poss_methods, population_size, min(tournament_size, population_size), max_method_calls, crossover_probability, mutation_probability, remove_probability, change_probability, insert_probability)
        archive = update_archive(parents, archive, relevant_targets)
        updated_targets = update_targets(parents, archive, relevant_targets)
        R = parents.union(offspring)

        tSuite = TestSuite(sc, accounts, deploying_accounts, _pop_size = population_size, _random = False, _tests = list(R), _max_method_calls=max_method_calls, _min_method_calls=min_method_calls)

        # We restart the Ganache blockchain for memory efficiency
        print("\tResetting Blockchain...")
        callstring = 'screen -p ganache -X stuff "^C"'
        os.system(callstring)
        callstring = 'screen -p ganache -X stuff "ganache-cli\r"'
        os.system(callstring)

        # Wait for Ganache to start, this takes about 3 seconds
        time.sleep(3)

        accounts, contract_json, contract_name, deployed_bytecode, bytecode, abi = get_ETH_properties(ETH_port, max_accounts, accounts_file_location, contract_json_location)
        if eval(config['Parameters']['deploying_accounts']) == []:
            deploying_accounts = accounts
        else:
            deploying_accounts = eval(config['Parameters']['deploying_accounts'])

        callstring = "node SC_interaction.js --methods".split() + [tSuite.generate_test_inputs()] + ["--abi"] + [abi] + ["--bytecode"] + [bytecode] + ["--ETH_port"] + [ETH_port]

        print("\tDeploying and testing...")
        subprocess.call(callstring)

        with open('debugs.txt', 'r') as f:
            callResults = f.read()

        with open('returnvals.txt', 'r') as f:
            returnvals = f.read().split(",")

        results = ast.literal_eval(callResults)

        print("\tUpdating test distances...")
        tSuite.update_test_distances(results, returnvals)

        Fs = preference_sorting(R, updated_targets, population_size)
        parents = set()
        dom_front = 0
        while len(parents) + len(Fs[dom_front]) < population_size:
            subvector_dist(Fs[dom_front], updated_targets)
            parents = parents.union(Fs[dom_front])
            dom_front += 1
        F = Fs[dom_front]
        subvector_dist(F, updated_targets)
        G = list(F)
        G.sort(key=lambda tCase: tCase.subvector_dist)
        parents = parents.union(set(G[:population_size - len(parents)]))
        assert len(parents) == population_size, "The set of new parents should be of a size equal to the population size."
        archives = archives + [archive]
        testSuites = testSuites + [tSuite]

        # Update the iteration counter
        iterations += 1

    archive = update_archive(parents, archive, relevant_targets)
    # print("Done")
    # with open("archives.p", "wb") as f:
    #     pickle.dump(archives, f)
    #
    # with open("testSuites.p", "wb") as f:
    #     pickle.dump(testSuites, f)
    runtime = datetime.datetime.now() - start_time
    return archives, tSuite, runtime.total_seconds(), iterations

def get_ETH_properties(ETH_port, max_accounts, accounts_file_location, contract_json_location):
    """
    Fetches relevant information for the deployment of and interaction with the smart contract.
    Inputs:
        - ETH_port: The port at which the Ethereum blockchain simulator is listening.
        - max_accounts: The number of accounts that can be used to interact with the blockchain.
        - accounts_file_location: The location of the file the accounts will be written to by the get_accounts.js procedure.
    Outputs:
        - accounts: The accounts on the blockchain that will be used for the deployment of and interaction with the smart contract.
    """
    callstring = "node get_accounts --ETH_port".split() + [ETH_port] + ["--max_accounts"] + ["{}".format(max_accounts)] + ["--accounts_file_location"] + [accounts_file_location]
    subprocess.call(callstring)
    with open(accounts_file_location) as f:
        res = f.read()
        accounts = res.split(',')

    with open(contract_json_location) as f:
        contract_json = json.load(f)

    contract_name =     contract_json['contractName']
    deployed_bytecode = contract_json['deployedBytecode']
    bytecode =          contract_json['bytecode']
    bytecode = '"' + contract_json['bytecode'] + '"'
    abi =               str(contract_json['abi'])
    abi = abi.replace("True", "true")
    abi = abi.replace("False", "false")
    return accounts, contract_json, contract_name, deployed_bytecode, bytecode, abi

def update_archive(tests, archive, relevant_targets):
    """
    Given an archive and a set of tests, replaces the archived tests by better tests.
    Inputs:
        - tests: The current generation of tests.
        - archive: The current list of best tests.
        - relevant_targets: Indicators of which tests are important for branch coverage.
    Outputs:
        - archive: The new and updated archive
    """
    for i, (best_test, relevant) in enumerate(zip(archive, relevant_targets)):
        if relevant:
            for test in tests:
                if test.distance_vector[i] == 0:
                    if best_test is None:
                        best_test = test
                    elif len(test.methodCalls)<len(best_test.methodCalls):
                        best_test = test
        archive[i] = best_test
    return archive

def update_targets(tests, archive, relevant_targets):
    """
    Identifies the targets that are reached but not satisfied by the current generation of tests.
    Inputs:
        - tests: The current generation of tests.
        - archive: The list of best test cases that satisfy specific targets.
        - relevant_targets: The list of targets that should be taken into account for branch coverage.
    Outputs:
        - updated_targets: The list of targets that are reached but not satisfied by the current generation of tests.
    """
    updated_targets = [False] * len(archive)
    for i, (best_test, relevant) in enumerate(zip(archive, relevant_targets)):
        if relevant:
            if best_test is not None:
                pass
            else:
                for test in tests:
                    if (test.distance_vector[i]>0) & (test.distance_vector[i]<=1):
                        updated_targets[i] = True
                        break
    return updated_targets

def determine_relevant_targets(compactEdges, compactNodes):
    """
    Nodes that end with the `REVERT' Opcode are a result of the Solidity code is compiled and are not relevant for our tests. This function identifies the edges leading to those nodes.
    Inputs:
        - compactEdges: The edges of the CDG of the smart contract.
        - compactNodes: The nodes of the CDG of the smart contract.
    Outputs:
        - relevant_targets: An ordered list of Booleans indicating whether each edge is relevant for branch coverage.
    """
    relevant_targets = [True] * len(compactEdges)
    for i, cEdge in enumerate(compactEdges):
        if "REVERT" == next((cNode.basic_blocks[-1].instructions[-1].name for cNode in compactNodes if cNode.node_id == cEdge.endNode_id), None):
            relevant_targets[i] = False
        elif cEdge.endNode_id[0] == "_fallback":
            relevant_targets[i] = False
        elif cEdge.startNode_id[0] == "_dispatcher":
            relevant_targets[i] = False
    return relevant_targets
