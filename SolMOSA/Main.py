"""
Run the experiment after soliciting the parameters and starting a blockchain \
instance, is called by ./Generate_Tests.sh.

Functions:
main             -- runs the experiment using the other modules and functions.
set_settings     -- prompts the user to specify certain parameters of the
 experiment.
show_settings    -- shows the settings, both from the config file and specified
 by the user. Called just before starting the experiments.
create_rapport   -- creates human-readable rapports to show the results,
 also writes the results to a .csv-file for computer interpretation.
log_du           -- logs the disk usage for debugging.
count_statements -- counts the number of statements in the smart contract under
 investigation.
"""

import configparser
import os
import subprocess
import logging
import csv
import re
# import sys

from pyfiglet import figlet_format

from SolMOSA import SolMOSA, determine_relevant_targets

logging.basicConfig(filename='SolMOSA.log', filemode='w', level=logging.DEBUG)


def main():
    """Run the experiment based on user-input and configuration."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config = configparser.ConfigParser()
    config.read(dir_path + "/Config.ini")
    affirmative = ["y", "Y", "yes", "Yes", "YES"]
    negative = ["n", "N", "no", "No", "NO"]
    ETH_port = config['Blockchain']['ETH_port']
    SmartContract_folder = dir_path + "/"\
        + config['Files']['SmartContract_folder'] + "/"
    config = set_settings(config, ETH_port, SmartContract_folder)
    SmartContract_folder = config['Files']['SmartContract_folder'] + "/"
    Rapports_folder = dir_path + "/" + config['Files']['rapports_folder']
    Execution_Times = int(config['Parameters']['execution_times'])
    memory_efficient = config['Parameters']['memory_efficient'] == "True"

    # Run SolMOSA and Create Rapports
    # Initialise the csv file for easy computer analysis
    columns = ["Name", "Tot. Statements", "Tot. Branches", "Branches Covered",
               "Generations", "Blockchain Time", "Offchain Time", "Total time"]
    with open("results.csv", mode="w") as f:
        f_writer = csv.writer(f, delimiter=',', quotechar="'",
                              quoting=csv.QUOTE_MINIMAL)
        f_writer.writerow(columns)

    # Create the rapports and fill out the csv file
    rapports = []
    for folder in os.listdir(SmartContract_folder):
        print("Smart Contract: {}".format(folder))
        for file in os.listdir(SmartContract_folder
                               + folder + "/build/contracts"):
            if file not in config['CFG']['Ignorefiles']:
                config.set('Files', 'contract_json_location', r'{}'.format(
                    os.path.abspath(SmartContract_folder + folder
                                    + "/build/contracts/" + file)))
                contractSolPath = SmartContract_folder + folder\
                    + "/contracts/" + file[:-4] + "sol"
                assert os.path.isfile(
                    contractSolPath), f"The name for the contract .json file \
                    '{file}' does not match it's .sol file: {contractSolPath}"
                config.set('Files', 'contract_sol_location',
                           r'{}'.format(contractSolPath))

                # Get the number of statements
                with open(contractSolPath, 'r') as f:
                    contractSol = f.read()
                statementCount = count_statements(contractSol)

                # Scrape the contract for hardcoded values.
                knownAddresses = eval(
                    config['Parameters']['deploying_accounts'])
                addresspool, ETHpool, intpool, stringpool = \
                    create_contractpools(contractSol, knownAddresses)
                config.set('Parameters', 'addresspool', repr(addresspool))
                config.set('Parameters', 'ETHpool', repr(ETHpool))
                config.set('Parameters', 'intpool', repr(intpool))
                config.set('Parameters', 'stringpool', repr(stringpool))

                # run SolMOSA on it with these settings.
                for i in range(Execution_Times):
                    archives, tSuite, run_time, blockchain_time, iterations\
                        = SolMOSA(config)
                    rapport = create_rapport(archives, tSuite, run_time,
                                             blockchain_time, iterations,
                                             folder, statementCount)
                    rapports = rapports + [rapport]
                    logging.info("Writing Rapport to {}".format(
                        Rapports_folder + "/" + folder + "_{}".format(i + 1)
                        + ".txt"))
                    with open(os.path.abspath(Rapports_folder + "/" + folder
                                              + "_{}".format(i + 1) + ".txt"),
                              'w') as f:
                        f.write(rapport)
                    if memory_efficient:
                        """
                        # We log the current size of our system and /tmp/
                        # folder in specific
                        """
                        logging.debug("Folder Sizes in / before resetting\
                         Ganache")
                        log_du("/")
                        logging.debug("Sizes in /tmp/")
                        log_du("/tmp/")
                        logging.debug("Folder Sizes in / before resetting\
                         Ganache")
                        log_du("/")
                        logging.debug("Sizes in /tmp/")
                        log_du("/tmp/")
                    # We restart the Ganache blockchain for memory efficiency
                    logging.info("\tResetting Blockchain...")
                    callstring = 'screen -S ganache -X stuff "^C"'
                    os.system(callstring)
                    if memory_efficient:
                        # Clear old blockchain from the /tmp directory
                        callstring = "rm -r /tmp/tmp-*"
                        subprocess.call(callstring, shell=True)
                        logging.debug("Folder Sizes in / after resetting\
                         Ganache")
                        log_du("/")
                        logging.debug("Sizes in /tmp/")
                        log_du("/tmp/")
                        logging.debug("Folder Sizes in / after resetting\
                         Ganache")
                        log_du("/")
                        logging.debug("Sizes in /tmp/")
                        log_du("/tmp/")
                    #  Start new instance of Ganache
                    callstring = 'screen -S ganache -X stuff "ganache-cli -d -e\
                     100000000000000\r"'
                    os.system(callstring)

    # After finishing all rapports ask to show rapports.
    proper_response = False
    while not proper_response:
        response = input("""Finished for all smart contracts.\nShow rapports\
         now? (y/n)""")
        if response in affirmative:
            proper_response = True
            for rapport in rapports:
                input("Press enter to show rapport...")
                print(rapport)
        elif response in negative:
            proper_response = True
        else:
            print('Please type "y" or "n" to confirm or deny.')
    print("Finished!")
    return


def set_settings(_config, _ETH_port, _SmartContract_folder):
    """Solicit final settings from user."""
    affirmative = ["y", "Y", "yes", "Yes", "YES"]
    negative = ["n", "N", "no", "No", "NO"]
    proper_response = False

    welcome_string = """Welcome to SolMOSA, the world's first meta-heuristic\
     test-case generator for Solidity-based Ethereuem smart contracts
    based on SolMOSA!\nThis script will guide you through the necessary steps\
     for the automated test-case generation.\n"""
    Ganache_string = """Would you like to start a Ganache client for easy\
     testing on GNU screen "ganache"? (y/n)"""
    ETH_port_string = """Please make sure you have a local blockchain running,\
     currently the settings expect the blockchain to be listening
    on port {}\n\nIs this still correct? (y/n)""".format(
        _ETH_port)
    SmartContract_location_string = """\nCurrently the tool will look for\
     smart contract json-files in "{}".\nIs this still correct? (y/n)"""\
     .format(os.path.abspath(_SmartContract_folder))
    Settings_string = """\nThe parameter settings can be changed by changing\
     the "Config.ini"-file located at {}.
    Would you like to display the parameter settings? (y/n)""".format(
        os.path.dirname(os.path.realpath(__file__)))

    print(figlet_format("SolMOSA"))
    print(welcome_string)

    # Give the user a chance to launch a ganache blockchain
    while not proper_response:
        response = input("{}".format(Ganache_string))
        if response in affirmative:
            # Launch a ganache-client in another screen
            callstring = 'screen -dmS ganache'
            os.system(callstring)
            callstring = 'screen -S ganache -X stuff "ganache-cli -d -e\
             100000000000000\r"'
            os.system(callstring)
            proper_response = True
            blockchain_running = True
        elif response in negative:
            proper_response = True
            blockchain_running = False
        else:
            print('Please type "y" or "n" to confirm or deny.')

    # Set the correct port for the listening local blockchain.
    proper_response = False
    while not proper_response | blockchain_running:
        response = input("{} ".format(ETH_port_string))
        if response in affirmative:
            proper_response = True
        elif response in negative:
            while not proper_response:
                response = input(
                    "\nPlease type the new port, you can either type 4 integers\
                     (e.g. 8545) or a full address. ")
                if (response.isdigit()) & (len(response) == 4):
                    ETH_port = "http://localhost:{}".format(response)
                else:
                    ETH_port = response
                response = input(
                    "I will use the port {} instead. Is this correct? (y/n) "
                    .format(ETH_port))
                if response in affirmative:
                    proper_response = True
                    _config.set('Blockchain', 'ETH_port', r'{}'
                                .format(ETH_port))
                elif response not in negative:
                    print('Please type "y" or "n" to confirm or deny.')
        else:
            print('Please type "y" or "n" to confirm or deny.')

    # Set the correct smart contract folder
    proper_response = False
    while not proper_response:
        response = input("{} ".format(SmartContract_location_string))
        if response in affirmative:
            proper_response = True
        elif response in negative:
            while not proper_response:
                response = input(
                    "\nPlease type the folder location, either as an absolute\
                     or a relative path. ")
                SmartContract_folder = response
                response = input('I will test the smart contracts in folder\
                 "{}" instead. Is this correct? (y/n) '.format(
                    os.path.abspath(SmartContract_folder)))
                if response in affirmative:
                    proper_response = True
                    _config.set('Files', 'SmartContract_folder', r'{}'.format(
                        os.path.abspath(SmartContract_folder)))
                elif response not in negative:
                    print('Please type "y" or "n" to confirm or deny.')
        else:
            print('Please type "y" or "n" to confirm or deny.')

    # Show settings if needed
    proper_response = False
    while not proper_response:
        response = input(Settings_string)
        if response in affirmative:
            print("")
            show_settings(_config)
            input("\nPress enter to start...\n")
            proper_response = True
        elif response in negative:
            print("")
            proper_response = True
        else:
            print('Please type "y" or "n" to confirm or deny.')

    return _config


def show_settings(config):
    """Show settings just before going into experimentation."""
    for setting in config['Parameters']:
        print("{}: {}".format(setting, config['Parameters'][setting]))


def create_rapport(archives, tSuite, run_time, blockchain_time, iterations,
                   folder, _statementCount):
    """
    Take the result of a test run and write a rapport.

    Inputs:
        - archives: The archive of each generation during the testing process
         (the last archive is the final test suite.)
        - tSuite: The test suite object at the end of the testing process.
        - run_time: The total time that it took to test a single smart contract
         once.
        - blockchain_time: The time spent on blockchain interaction during the
         total run time.
        - iterations: The number of iterations it took to reach branch coverage
         if branch coverage was achieved.
        The maximum number of generations otherwise
    Output:
        - A human-readable rapport file is created
        - The main results are added to a csv file for easy processing.
    """
    contractName = tSuite.smartContract.contractName
    relevant_branches = determine_relevant_targets(
        tSuite.smartContract.CDG.CompactEdges,
        tSuite.smartContract.CDG.CompactNodes)
    if sum(relevant_branches) == 0:
        with open("results.csv", "a") as f:
            f_writer = csv.writer(f, delimiter=',', quotechar="'",
                                  quoting=csv.QUOTE_MINIMAL)
            f_writer.writerow([contractName, 1, _statementCount, 1, iterations,
                               blockchain_time,
                               run_time - blockchain_time, run_time])
        return "No branches found, any method call will work!"
    else:
        best_tests = [best_test for best_test, relevant in zip(
            archives[-1], relevant_branches) if relevant]
        try:
            h = tSuite.smartContract.methods[0]['stateMutability']
        except:
            h = "Old version."
        rapport = """Contract:\t\t\t{}\n\n
        Number of Relevant Branches:\t{}\n
        Number of Branches Covered:\t\t{}\n
        Runtime: \t\t\t\t\t\t\t\t\t\t\t{}\n
        Blockchain Time: \t\t\t\t\t\t\t{}\n
        Iterations\t\t\t\t\t\t\t\t\t\t
        {}\n\n--------------------------------------------------\n
        METHODS:\n\n
        Constructor:\n\tInputs :{}\n
        \tPayable: {}"""\
        .format(
            contractName, sum(relevant_branches), len(
                [best_test for best_test in best_tests
                 if best_test is not None]),
            run_time, blockchain_time, iterations,
            tSuite.smartContract.methods[0]['inputs'], h)
        for method in tSuite.smartContract.methods[1:]:
            methodstring = """\n{}:\n
            \tInputs: {}\n
            \tOutputs: {}\n
            \tPayable: {}""".format(
                method['name'], method['inputs'], method['outputs'],
                method['payable'])
            rapport = rapport + methodstring

        shown_tests = []
        rapport = rapport\
            + """\n\n--------------------------------------------------\n
            TESTS:"""
        archive = archives[-1]
        for testCase in archive:
            # ADD THIS:  & (testCase not in shown_tests)
            if (testCase is not None):
                shown_tests = shown_tests + [testCase]
                teststring = """\n"""
                for i, methodCall in enumerate(testCase.methodCalls):
                    methodcallstring = """\n\t({}) {}({}, from: {},
                    value: {})""".format(
                        i + 1, methodCall.methodName, methodCall.inputvars,
                        methodCall.fromAcc, methodCall.value)
                    if methodCall.methodName != 'constructor':
                        methodcallstring = methodcallstring + \
                            """\tReturns: {}""".format(testCase.returnVals[i])
                    teststring = teststring + methodcallstring
                rapport = rapport + teststring

        with open("results.csv", "a") as f:
            f_writer = csv.writer(f, delimiter=',', quotechar="'",
                                  quoting=csv.QUOTE_MINIMAL)
            f_writer.writerow([folder, sum(relevant_branches), _statementCount,
                               len(
                [best_test for best_test in best_tests
                 if best_test is not None]), iterations, blockchain_time,
                run_time - blockchain_time, run_time])

        return rapport


def log_du(path):
    """Log disk usage in human readable format (e.g. '2,1GB')."""
    for file in os.listdir(path):
        logging.debug(
            "file" + subprocess.check_output(['du', '-hcs', path + file])
            .split()[0].decode('utf-8'))


def count_statements(_contractSol):
    """Count the number of statements in a .sol file."""
    regex = r""";(?=([^\"\']*[\"\'][^\"\']*\")*[^\"\']*$)"""
    return sum(1 for m in re.finditer(regex, _contractSol, re.MULTILINE))


def create_contractpools(_contractSol, _known_addresses):
    """
    Scrapes the solidity code for hardcoded values and adds these to\
     input pools that are used later on whenever a random method is created.

    Arguments:
        - _contractSol:     The solidity code of the smart contract
        - _known_addresses: The addresses that exist on the Blockchain.

    Outputs:
        - addresspool: The pool of scraped addresses, cannot contain any
                       address that is not in _known_addresses.
        - ETHpool:     The pool of scraped ethereum values.
        - intpool:     The pool of scraped integers.
        - stringpool:  The pool of scraped strings, ignores error messages that
                       come in revert- or require statements.
    """
    contractSol = _contractSol
    if len(_known_addresses) > 0:
        addresspool = scrape_addresses(contractSol)
    else:
        addresspool = set()
    assert addresspool.intersection(_known_addresses) == addresspool,\
        "A hardcoded address was found that does not exist on the\
    blockchain used."
    ETHpool = scrape_vals(contractSol)
    intpool = scrape_ints(contractSol)
    stringpool = scrape_strings(contractSol)
    return addresspool, ETHpool, intpool, stringpool


def scrape_addresses(_contractSol):
    """Scrape the .sol-file for any hardcoded addresses."""
    contractSol = _contractSol
    addresspool = set()
    regex = r"0x[A-Za-z0-9]{40}"
    addressMatches = re.finditer(regex, contractSol, re.MULTILINE)
    for match in addressMatches:
        addresspool.add(match.group())
    return addresspool


def scrape_vals(_contractSol):
    """Scrape the .sol-file for any hardcoded values."""
    contractSol = _contractSol
    ETHpool = set()
    regex = r"[0-9]*\.?[0-9]+\s*(wei|szabo|finney|ether)"
    valMatches = re.finditer(regex, contractSol, re.MULTILINE)
    for match in valMatches:
        regex = r"[0-9]*\.?[0-9]+"
        val = float(re.search(regex, match.group()).group())
        if match.group()[-3:] == "wei":
            assert val % 1 == 0, "A non-integer wei value was found: {}"\
                .format(val)
            ETHpool.add(int(val))
        elif match.group()[-5:] == "szabo":
            val = val * 10**12
            assert val % 1 == 0, "A non-integer wei value was found: {}"\
                .format(val)
        elif match.group()[-5:] == "ether":
            val = val * 10**18
            assert val % 1 == 0, "A non-integer wei value was found: {}"\
                .format(val)
        else:
            # match corresponds to "finney"
            val = val * 10**15
            assert val % 1 == 0, "A non-integer wei value was found: {}"\
                .format(val)
        ETHpool.add(val)
    return ETHpool


def scrape_ints(_contractSol):
    """Scrape the .sol-file for any hardcoded integers."""
    contractSol = _contractSol
    intpool = set()

    # Remove any lines with pragma for the purpose of scraping ints.
    regex = r"(pragma solidity)\s*[\ˆ\^]?[0-9\.]*"
    pragmaMatch = re.search(regex, contractSol, re.MULTILINE)
    while pragmaMatch:
        contractSol = contractSol[:pragmaMatch.span()[0]]\
            + contractSol[pragmaMatch.span()[1]:]
        pragmaMatch = re.search(regex, contractSol, re.MULTILINE)

    # Ignore integers that follow an int or uint declaration.
    regex = r"-?(?<![(int)\d])\d+"
    intMatches = re.finditer(regex, contractSol, re.MULTILINE)
    for match in intMatches:
        intpool.add(int(match.group()))
    return intpool


def scrape_strings(_contractSol):
    """Scrape the .sol-file for any hardcoded strings."""
    contractSol = _contractSol
    stringpool = set()

    # Remove error messages inside require or revert statements.
    regex = r"(require)|(revert)"
    errorMatch = re.search(regex, contractSol, re.MULTILINE)
    start = 0
    while errorMatch:
        contractSol, new_start = remove_errorStrings(contractSol, 0,
                                                     errorMatch.end() + start)
        start = new_start
        errorMatch = re.search(regex, contractSol[start:], re.MULTILINE)

    regex = r"(?<!import )([\"'])(?:(?=(\\?))\2.)*?\1"
    matches = re.finditer(regex, contractSol, re.MULTILINE)
    for match in matches:
        stringpool.add(match.group())
    return stringpool


def remove_errorStrings(_contractSol, _brack_ctr, _pos):
    """Remove the errorstring from a require or revert statement, if it is \
    present.

    Arguments:
    _contractSol:   the current string of the .sol file.
    _brack_ctr:     counter that indicates whether a require or revert is \
                    open or closed.
    _pos:           the index of the string where the algorithm starts looking.
    """
    assert _brack_ctr >= 0, "The bracket counter cannot be smaller than 0!"
    regex = r"[\(\)\n]"
    match = re.search(regex, _contractSol[_pos:])
    found = match.group()
    assert found is not None, "Nothing was found!"
    pos = _pos + match.span()[0]
    if found == "\n":
        #         Nothing needs to be removed
        return _contractSol, pos + 1
    elif found == "(":
        #         We're going deeper into the land of parentheses
        brack_ctr = _brack_ctr + 1
        position = pos + 1
        return remove_errorStrings(_contractSol, brack_ctr, position)
    elif found == ")":
        #         We're leaving the land of parentheses
        brack_ctr = _brack_ctr - 1
        if brack_ctr == 0:
            regex = r"([\"'])(?:(?=(\\?))\2.)*?\1\s*\)\Z"
            errorstring = re.search(regex, _contractSol[:pos + 1])
            if errorstring:
                # An errorstring was found and can be removed
                _contractSol = _contractSol[:errorstring.span()[0]] + \
                    _contractSol[errorstring.span()[1]:]
                return _contractSol, match.span()[0]
            else:
                return _contractSol, pos + 1

        else:
            position = pos + 1
            return remove_errorStrings(_contractSol, _brack_ctr, position)
    else:
        assert False, "Found unexpected pattern: {}".format(found)


main()
