import os
from SolMOSA import *

def Test_Ganache_reset(config):

    dir_path = os.path.dirname(os.path.realpath(__file__))
    ETH_port = config['Blockchain']['ETH_port']
    max_accounts = int(config['Parameters']['max_accounts'])
    accounts_file_location = dir_path + "/" + config['Files']['accounts_file_location']
    contract_json_location = config['Files']['contract_json_location']

    # print("Starting Ganache")
    # # Launch a ganache-client in another screen
    # callstring = 'screen -dmS ganache'
    # os.system(callstring)
    # callstring = 'screen -S ganache -X stuff "ganache-cli\r"'
    # os.system(callstring)

    accounts, contract_json, contract_name, deployed_bytecode, bytecode, abi = get_ETH_properties(ETH_port, max_accounts, accounts_file_location, contract_json_location)

    response = input("Check the /tmp directory now and press enter when finished")

    # We restart the Ganache blockchain for memory efficiency
    print("\tResetting Blockchain...")
    callstring = 'screen -S ganache -X stuff "^C"'
    os.system(callstring)
    # Clear old blockchain from the /tmp directory
    callstring = "rm -r /tmp/tmp-*"
    subprocess.call(callstring, shell=True)
    #  Start new instance of Ganache
    callstring = 'screen -S ganache -X stuff "ganache-cli\r"'
    os.system(callstring)
