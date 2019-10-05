# Prerequisites:
# contracts have been compiled and their location is stored in CFG_config.ini
# Ganache is running and the Ganache accounts have been stored in Main_config.ini

from DynaMOSA import *
from CDG import *
from Test_Suite import *
from Preference_Sorting import *
from Generate_Offspring import *
from pyfiglet import figlet_format
import json, pickle, configparser, os, json, ast, subprocess, sys, datetime

def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config = configparser.ConfigParser()
    config.read(dir_path+"/Config.ini")
    affirmative = ["y", "Y", "yes", "Yes", "YES"]
    negative = ["n", "N", "no", "No", "NO"]
    ETH_port = config['Blockchain']['ETH_port']
    SmartContract_folder = dir_path + "/"+config['Files']['SmartContract_folder']
    config = set_settings(config, ETH_port, SmartContract_folder)
    Rapports_folder = dir_path + "/" + config['Files']['rapports_folder']
    Execution_Times = int(config['Parameters']['execution_times'])

    # Run DynaMOSA and Create Rapports
    rapports = []
    for folder in os.listdir(SmartContract_folder):
        for file in os.listdir(SmartContract_folder+folder+"/build/contracts"):
            if file not in config['CFG']['Ignorefiles']:
                config.set('Files','contract_json_location',r'{}'.format(os.path.abspath(SmartContract_folder+folder+"/build/contracts""/"+file)))
                # run DynaMOSA on it with these settings.
                for i in range(Execution_Times):
                    archives, tSuite, run_time, iterations = DynaMOSA(config)
                    rapport = create_rapport(archives, tSuite, run_time, iterations)
                    rapports = rapports + [rapport]
                    print("Writing Rapport to {}".format(Rapports_folder+"/"+folder+"_{}".format(i+1)+".txt"))
                    with open(os.path.abspath(Rapports_folder+"/"+folder+"_{}".format(i+1)+".txt"), 'w') as f:
                        f.write(rapport)

    # After finishing one rapport ask to show rapports.
    proper_response = False
    while not proper_response:
        response = input("""Finished for all smart contracts.\nShow rapports now? (y/n)""")
        if response in affirmative:
            proper_response = True
            for rapport in rapports:
                input("Press any key to show rapport...")
                print(rapport)
        elif response in negative:
            proper_response = True
        else:
            print('Please type "y" or "n" to confirm or deny.')
    print("Finished!")
    return

def set_settings(_config, _ETH_port, _SmartContract_folder):
    affirmative = ["y", "Y", "yes", "Yes", "YES"]
    negative = ["n", "N", "no", "No", "NO"]
    proper_response = False

    welcome_string = """Welcome to SolMOSA, the world's first meta-heuristic test-case generator for Solidity-based Ethereuem smart contracts based on DynaMOSA!\nThis script will guide you through the necessary steps for the automated test-case generation.\n"""
    ETH_port_string  = """Please make sure you have a local blockchain running, currently the settings expect the blockchain to be listening on port {}\n\nIs this still correct? (y/n)""".format(_ETH_port)
    SmartContract_location_string = """\nCurrently the tool will look for smart contract json-files in "{}".\nIs this still correct? (y/n)""".format(os.path.abspath(_SmartContract_folder))
    Settings_string = """\nThe parameter settings can be changed by changing the "Config.ini"-file located at {}. Would you like to display the parameter settings? (y/n)""".format(os.path.dirname(os.path.realpath(__file__)))

    print(figlet_format("SolMOSA"))
    print(welcome_string)

    # Set the correct port for the listening local blockchain.
    while not proper_response:
        response = input("{} ".format(ETH_port_string))
        if response in affirmative:
            proper_response = True
        elif response in negative:
            while not proper_response:
                response = input("\nPlease type the new port, you can either type 4 integers (e.g. 8545) or a full address. ")
                if (response.isdigit()) & (len(response) == 4):
                    ETH_port = "http://localhost:{}".format(response)
                else:
                    ETH_port = response
                response = input("I will use the port {} instead. Is this correct? (y/n) ".format(ETH_port))
                if response in affirmative:
                    proper_response = True
                    config.set('Blockchain','ETH_port',r'{}'.format(ETH_port))
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
                response = input("\nPlease type the folder location, either as an absolute or a relative path. ")
                SmartContract_folder = response
                response = input('I will use the smart contract "{}" instead. Is this correct? (y/n) '.format(os.path.abspath(SmartContract_folder)))
                if response in affirmative:
                    proper_response = True
                    config.set('Files','SmartContract_folder',r'{}'.format(os.path.abspath(SmartContract_folder)))
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
            input("\nPress any key to start...\n")
            proper_response = True
        elif response in negative:
            print("")
            proper_response = True
        else:
            print('Please type "y" or "n" to confirm or deny.')

    return _config

def show_settings(config):
    for setting in config['Parameters']:
        print("{}: {}".format(setting, config['Parameters'][setting]))

def create_rapport(archives, tSuite, run_time, iterations):
    contractName = tSuite.smartContract.contractName
    relevant_branches = determine_relevant_targets(tSuite.smartContract.CDG.CompactEdges, tSuite.smartContract.CDG.CompactNodes)
    if sum(relevant_branches) == 0:
        return "No branches found, any method call will work!"
    best_tests = [best_test for best_test, relevant in zip(archives[-1], relevant_branches) if relevant]
    rapport = """Contract:\t\t\t{}\n\nNumber of Relevant Branches:\t{}\nNumber of Branches Covered:\t\t{}\nRuntime: \t\t\t\t\t\t\t\t\t\t\t{}\nIterations\t\t\t\t\t\t\t\t\t\t{}\n\n--------------------------------------------------\nMETHODS:\n\nConstructor:\n\tInputs :{}\n\tPayable: {}""".format(contractName, sum(relevant_branches), len([best_test for best_test in best_tests if best_test is not None]), run_time, iterations, tSuite.smartContract.methods[0]['inputs'], tSuite.smartContract.methods[0]['stateMutability'])
    for method in tSuite.smartContract.methods[1:]:
        methodstring = """\n{}:\n\tInputs: {}\n\tOutputs: {}\n\tPayable: {}""".format(method['name'], method['inputs'], method['outputs'], method['payable'])
        rapport = rapport + methodstring
    shown_tests = []
    rapport = rapport + """\n\n--------------------------------------------------\nTESTS:"""
    archive = archives[-1]
    for testCase in archive:
        if (testCase is not None) & (testCase not in shown_tests):
            shown_tests = shown_tests + [testCase]
            teststring = """\n"""
            for i, methodCall in enumerate(testCase.methodCalls):
                methodcallstring = """\n\t({}) {}({}, from: {}, value: {})""".format(i+1, methodCall.methodName, methodCall.inputvars, methodCall.fromAcc, methodCall.value)
                if methodCall.methodName != 'constructor':
                    methodcallstring = methodcallstring + """\tReturns: {}""".format(testCase.returnVals[i])
                teststring = teststring + methodcallstring
            rapport = rapport + teststring
    return rapport

main()
