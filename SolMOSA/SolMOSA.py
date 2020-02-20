"""
The python implementation of SolMOSA that works on compiled Solidity \
Smart Contracts.

Prerequisites:
    - An Ethereum blockchain simulator should be running.
    - All the settings need to be specified in a config file
"""
import os
import json
import ast
import subprocess
import datetime
import logging
import numpy as np
# import pickles
import sys

from CDG import CDG
from SmartContract import SmartContract
from Test_Suite import TestSuite
from Preference_Sorting import preference_sorting, subvector_dist
from Generate_Offspring import generate_offspring

np.set_printoptions(threshold=sys.maxsize)


def SolMOSA(config):
    """
    Apply genetic algorithm to iteratively generate an optimal test suite.

    Arguments:
        - config_file_location: The location of a config_file that specifies \
        all the parameters necessary for the SolMOSA algorithm.
    Outputs:
        - archives: A list containing the best test cases for each branch at \
        each generation of the algorithm,
        the final archive in the list contains the best test cases found by \
        the algorithm.
        - tSuite: The TestSuite object that was used by the SolMOSA algorithm.
        - runtime: The time it took to generate the tests.
        - iterations: The number of times the genetic loop was executed.
    """
    # Register the time when the algorithm starts
    start_time = datetime.datetime.now()
    dir_path = os.path.dirname(os.path.realpath(__file__))

    # Read Configuration. Parameters for initiating the Blockchain.
    ETH_port = config['Blockchain']['ETH_port']
    max_accounts = int(config['Parameters']['max_accounts'])
    accounts_file_location = dir_path + "/"\
        + config['Files']['accounts_file_location']

    # Parameters for creating a Control-Dependency-Graph
    contract_json_location = config['Files']['contract_json_location']
    predicates = eval(config['CFG']['Predicates'])

    # Parameters for creating Test-Cases
    population_size = int(config['Parameters']['population_size'])
    max_method_calls = int(config['Parameters']['max_method_calls'])
    min_method_calls = int(config['Parameters']['min_method_calls'])
    maxWei = int(config['Parameters']['maxWei'])
    addresspool = eval(config['Parameters']['addresspool'])
    ETHpool = eval(config['Parameters']['ETHpool'])
    intpool = eval(config['Parameters']['intpool'])
    stringpool = eval(config['Parameters']['stringpool'])
    passBlocks = config['Parameters']['passBlocks'] == "True"
    passTime = config['Parameters']['passTime'] == "True"
    passTimeTime = int(config['Parameters']['passTimeTime'])
    ignorefunctionNames = eval(config['Parameters']['IgnoreFunctions'])
    ignoreStateVariables = eval(config['Parameters']['ignoreStateVariables'])

    # Parameters for mutating test cases
    crossover_probability\
        = float(config['Parameters']['crossover_probability'])
    remove_probability = float(config['Parameters']['remove_probability'])
    change_probability = float(config['Parameters']['change_probability'])
    insert_probability = float(config['Parameters']['insert_probability'])
    tournament_size = int(config['Parameters']['tournament_size'])

    # Parameters that specify the scope of the experiment
    search_budget = int(config['Parameters']['search_budget'])
    memory_efficient = config['Parameters']['memory_efficient'] == "True"

    accounts, contract_json, contract_name, deployed_bytecode, bytecode, abi\
        = get_ETH_properties(ETH_port, max_accounts, accounts_file_location,
                             contract_json_location)

    if eval(config['Parameters']['deploying_accounts']) == []:
        deploying_accounts = accounts
    else:
        deploying_accounts = eval(config['Parameters']['deploying_accounts'])

    if ignoreStateVariables:
        ignorefunctionNames = update_ignoreFunctionNames(
            ignorefunctionNames, contract_json)
    if len(ignorefunctionNames) > 0:
        logging.info(f"Ignoring the following functions: ")
        for ignoreFunctionName in ignorefunctionNames:
            logging.info(f"{ignoreFunctionName}")

    # Create the CDG
    cdg = CDG(contract_name, deployed_bytecode, predicates)
    cdg.LT(predicates)
    logging.info("Contract CDG has been created and looks as follows:\n")
    cdg.Show_CDG(log=True)

    sc = SmartContract(contract_json, cdg, ignorefunctionNames)

    tSuite = TestSuite(sc, accounts, deploying_accounts,
                       _addresspool=addresspool,
                       _ETHpool=ETHpool,
                       _intpool=intpool,
                       _stringpool=stringpool,
                       _pop_size=population_size, _random=True, _tests=[],
                       _max_method_calls=max_method_calls,
                       _min_method_calls=min_method_calls,
                       _passBlocks=passBlocks, _passTime=passTime,
                       _passTimeTime=passTimeTime, _maxWei=maxWei)

    logging.info("Smart Contract Under investigation: {}"
                 .format(contract_json_location))
    relevant_targets = determine_relevant_targets(
        cdg.CompactEdges, ignorefunctionNames, log=True)

    if sum(relevant_targets) == 0:
        logging.info("No branching paths were detected!")
        return [], tSuite, (datetime.datetime.now()
                            - start_time).total_seconds(), 0, 0

    test_inputs = tSuite.generate_test_inputs()
    with open("tests.txt", "w") as f:
        f.write(test_inputs)

    callstring = "node SC_interaction.js".split(
    ) + ["--abi"] + [abi] + ["--bytecode"] + [bytecode] + ["--ETH_port"]\
        + [ETH_port]

    blockchain_start_time = datetime.datetime.now()
    logging.info("Deploying and calling smart contracts for the first time...")
    with open("Ganache_Interaction.log", "a") as f:
        subprocess.call(callstring, stdout=f)
    blockchain_end_time = datetime.datetime.now()
    blockchain_time = blockchain_end_time - blockchain_start_time

    logging.info("Reading results...")
    with open('debugs.txt', 'r') as f:
        callResults = f.read()

    with open('returnvals.txt', 'r') as f:
        returnvals = f.read().split(",")

    results = ast.literal_eval(callResults)

    logging.info("Updating test distances...")
    tSuite.update_test_distances(results, returnvals)

    init_archive = [None] * len(tSuite.smartContract.CDG.CompactEdges)
    parents = set(tSuite.tests)

    archive = update_archive(parents, init_archive, relevant_targets,
                             tSuite.smartContract.CDG.CompactEdges)
    archives = [archive]
    testSuites = [tSuite]
    updated_targets = update_targets(parents, archive, relevant_targets)

    Fs = preference_sorting(parents, updated_targets, population_size)

    for F in Fs:
        subvector_dist(F, updated_targets)

    poss_methods = tSuite.smartContract.methods[1:]

    # Keep track of number of iterations necessary to achieve branch coverage
    iterations = 0

    for i in range(search_budget):
        logging.info("\nEntering main loop iteration {}/{} at {}:{}"
                     .format(i + 1,
                             search_budget, datetime.datetime.now().date(),
                             datetime.datetime.now().time()))

        logging.info("{} out of {} branches have been covered"
                     .format(len([test for test, relevant in
                                  zip(archive, relevant_targets) if
                                  (test is not None) & (relevant)]),
                             len([test for test, relevant in
                                  zip(archive, relevant_targets) if
                                  relevant])))
    #    logging.debug("The relevant Edges at this point should be:")
    #    for tempEdge in [edge for edge, relevant in
    #                     zip(cdg.CompactEdges, relevant_targets) if relevant]:
    #        tempEdge.show_CompactEdge(True)
    #    logging.info("The following test cases are currently in the Archive:")
    #    for best_test in [best_test for best_test, relevant in
    #                      zip(archive, relevant_targets) if relevant]:
    #            best_test.show_test(log=True)
    #            logging.info("")

        # Cancel if branch coverage has already been achieved.
        # Otherwise, log the branches that still need to be covered.
        finished = True
        for k, relTest in enumerate(archive):
            if (relTest is None) & (relevant_targets[k]):
                logging.info("Still need to cover:")
                cdg.CompactEdges[k].show_CompactEdge(log=True)
                finished = False
        if finished:
            if i == 0:
                logging.info("Branch coverage was achieved after random\
                             initialisation")
            else:
                logging.info("Branch coverage was achieved at iteration {}"
                             .format(i))
            break

        # Update the iteration counter
        iterations += 1

        logging.info("\tGenerating Offspring...")
        offspring = generate_offspring(
            parents, sc, accounts, addresspool, ETHpool, intpool, stringpool,
            deploying_accounts, poss_methods, population_size, min(
                tournament_size, population_size), max_method_calls,
            crossover_probability, remove_probability, change_probability,
            insert_probability, passTimeTime, maxWei)

        tSuite = TestSuite(sc, accounts, deploying_accounts,
                           _addresspool=addresspool, _ETHpool=ETHpool,
                           _intpool=intpool, _stringpool=stringpool,
                           _pop_size=population_size, _random=False,
                           _tests=list(offspring),
                           _max_method_calls=max_method_calls,
                           _min_method_calls=min_method_calls)

        test_inputs = tSuite.generate_test_inputs()
        with open("tests.txt", "w") as f:
            f.write(test_inputs)

        logging.info("\tDeploying and testing...")

        blockchain_start_time = datetime.datetime.now()
        if memory_efficient:
            if i % 10 == 1:
                # We restart the Ganache blockchain for memory efficiency
                logging.info("\tResetting Blockchain...")
                callstring = 'screen -S ganache -X stuff "^C"'
                os.system(callstring)
                # Clear old blockchain from the /tmp directory
                callstring = "rm -r /tmp/tmp-*"
                subprocess.call(callstring, shell=True)
                #  Start new instance of Ganache with a ridiculus amount of
                # ether for each account
                callstring = 'screen -S ganache -X stuff \
                "ganache-cli -d -e 100000000000000000000\r"'
                os.system(callstring)
                callstring = "node get_accounts --ETH_port".split()\
                    + [ETH_port] + ["--max_accounts"]\
                    + ["{}".format(max_accounts)]\
                    + ["--accounts_file_location"] + [accounts_file_location]
                with open("Ganache_Interaction.log", "a") as f:
                    subprocess.call(callstring, stdout=f)

        callstring = "node SC_interaction.js".split() + ["--abi"] + [abi]\
            + ["--bytecode"] + [bytecode] + ["--ETH_port"] + [ETH_port]

        with open("Ganache_Interaction.log", "a") as f:
            subprocess.call(callstring, stdout=f)
        blockchain_time += datetime.datetime.now() - blockchain_start_time

        with open('debugs.txt', 'r') as f:
            callResults = f.read()

        with open('returnvals.txt', 'r') as f:
            returnvals = f.read().split(",")

        results = ast.literal_eval(callResults)

        logging.info("\tUpdating test distances...")
        tSuite.update_test_distances(results, returnvals)

        archive = update_archive(offspring, archive, relevant_targets,
                                 tSuite.smartContract.CDG.CompactEdges)
        updated_targets = update_targets(offspring, archive, relevant_targets)
        R = parents.union(offspring)

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
        assert len(parents) == population_size,\
            "The set of new parents should be of a size equal to the \
            population size."
        archives = archives + [archive]
        testSuites = testSuites + [tSuite]

    archive = update_archive(parents, archive, relevant_targets,
                             tSuite.smartContract.CDG.CompactEdges)
    runtime = datetime.datetime.now() - start_time
    return archives, tSuite, runtime.total_seconds(), \
        blockchain_time.total_seconds(), iterations


def update_ignoreFunctionNames(_ignorefunctionNames, _contract_json):
    """Add the stateVariables to the ignorefunctionNames."""
    ignorefunctionNames = _ignorefunctionNames
    contract_json = _contract_json
    stateVariables = []
    infoNode = next((node for node in contract_json['ast']['nodes'] if
                     node['nodeType'] == "ContractDefinition"), None)
    for node in infoNode['nodes']:
        if "stateVariable" in node.keys():
            name = node["name"]
            if not node["stateVariable"]:
                logging.warning(f"There was a node with stateVariable in the "
                                "json but the value is not True!")
            else:
                recurNode = node["typeName"]
                inputvars = ""
                while recurNode['nodeType'] == "Mapping":
                    if len(inputvars) > 1:
                        inputvars = inputvars + ","
                    assert "keyType" in recurNode.keys(), \
                        "A mapping node was found without a 'typeName' field"
                    assert "valueType" in recurNode.keys(), \
                        "A mapping node was found without a 'valueType' field"
                    inputvars = inputvars + recurNode["keyType"]["name"]
                    recurNode = recurNode["valueType"]
                stateVariables.append(name + "(" + inputvars + ")")
    return list(set(ignorefunctionNames).union(set(stateVariables)))


def get_ETH_properties(ETH_port, max_accounts, accounts_file_location,
                       contract_json_location):
    """
    Fetch relevant information for the deployment of and interaction with the\
    smart contract.

    Arguments:
    ETH_port:       The port at which the Ethereum blockchain simulator is
                    listening.
    max_accounts:   The number of accounts that can be used to interact with
                    the blockchain.
    accounts_file_location: The location of the file the accounts will be
                            written to by the get_accounts.js procedure.
    Outputs:
    accounts:   The accounts on the blockchain that will be used for the
                deployment of and interaction with the smart contract.
    """
    callstring = "node get_accounts --ETH_port".split() + [ETH_port]\
        + ["--max_accounts"] + ["{}".format(max_accounts)]\
        + ["--accounts_file_location"] + [accounts_file_location]
    with open("Ganache_Interaction.log", "w") as f:
        subprocess.call(callstring, stdout=f)
    with open(accounts_file_location) as f:
        res = f.read()
        accounts = res.split(',')

    with open(contract_json_location) as f:
        contract_json = json.load(f)

    contract_name = contract_json['contractName']
    deployed_bytecode = contract_json['deployedBytecode']
    bytecode = contract_json['bytecode']
    bytecode = '"' + contract_json['bytecode'] + '"'
    abi = str(contract_json['abi'])
    abi = abi.replace("True", "true")
    abi = abi.replace("False", "false")
    return accounts, contract_json, contract_name, \
        deployed_bytecode, bytecode, abi


def update_archive(tests, archive, relevant_targets, _edges):
    """
    Replace the archived tests by better tests, given an archive and a set of \
    potentially better tests.

    Arguments:
    tests:              The current generation of tests.
    archive:            The current list of best tests.
    relevant_targets:   Indicators of which tests are important for branch
                        coverage.
    Outputs:
    archive:    The new and updated archive
    """
    j = 0
    for i, (best_test, relevant) in enumerate(zip(archive, relevant_targets)):
        if relevant:
            for test in tests:
                if test.distance_vector[i] == 0:
                    if best_test is None:
                        logging.info(
                            f"There was no best test yet for relevant_target "
                            f"{j} with edge:\n")
                        _edges[i].show_CompactEdge(log=True)
                        logging.info(f"now entering the archive is test: \n")
                        test.show_test(log=True)
                        best_test = test
                    elif len(test.methodCalls) < len(best_test.methodCalls):
                        logging.info(
                            f"A better test was found for relevant_target {i} "
                            "with edge:\n")
                        _edges[i].show_CompactEdge(log=True)
                        logging.info(f"the old test was:\n")
                        best_test.show_test(log=True)
                        logging.info("\nThe new test is:\n")
                        test.show_test(log=True)
                        best_test = test
            j += 1
        archive[i] = best_test
    return archive


def update_targets(tests, archive, relevant_targets):
    """
    Identify the targets that are reached but not satisfied by the current \
    generation of tests.

    Inputs:
    tests:              The current generation of tests.
    archive:            The list of best test cases that satisfy specific
                        targets.
    relevant_targets:   The list of targets that should be taken into account
                        for branch coverage.
    Outputs:
    updated_targets:    The list of targets that are reached but not satisfied
                        by the current generation of tests.
    """
    updated_targets = [False] * len(archive)
    for i, (best_test, relevant) in enumerate(zip(archive, relevant_targets)):
        if relevant:
            if best_test is not None:
                pass
            else:
                for test in tests:
                    if (test.distance_vector[i] > 0) & \
                            (test.distance_vector[i] <= 1):
                        updated_targets[i] = True
                        break
    return updated_targets


def determine_relevant_targets(_compactEdges, _ignorefunctionNames, log=False):
    """
    We don't really care for edges in the dispactcher or the fallback \
    function if it has not been explicitly defined.

    Inputs:
    _compactEdges: The edges of the CDG of the smart contract.
    log:           Indication of whether the relevant targets should be logged.
    Outputs:
    relevant_targets: An ordered list of Booleans indicating whether each edge
                      is relevant for branch coverage.
    """
    relevant_targets = [True] * len(_compactEdges)
    for i, cEdge in enumerate(_compactEdges):
        if (cEdge.endNode_id[0] == "_fallback") | \
                (cEdge.endNode_id[0] == "_dispatcher") | \
                (cEdge.startNode_id[0] in _ignorefunctionNames) | \
                (cEdge.endNode_id[0] in _ignorefunctionNames):
            relevant_targets[i] = False
    if log:
        logging.info("Relevant targets have been identified as follows: \n")
        j = 0
        for relevant, cEdge in zip(relevant_targets, _compactEdges):
            if relevant:
                logging.info(f"Target {j}")
                cEdge.show_CompactEdge(log=True)
                j += 1
    return relevant_targets


def show_relevant_targets(_compactEdges, _relevant_targets):
    """Show the relevant targets and their order."""
    logging.debug("Showing Relevant Targets")
    for cEdge, rt in zip(_compactEdges, _relevant_targets):
        if rt:
            cEdge.show_CompactEdge(log=True)


def log_du(path):
    """Log disk usage in human readable format (e.g. '2,1GB')."""
    for file in os.listdir(path):
        logging.debug(
            "file" + subprocess.check_output(['du', '-hcs', path + file])
            .split()[0].decode('utf-8'))
