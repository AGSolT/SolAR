# SolAR
SolAR is a tool that generates full test suites that are optimised for [](branch coverage) first, and minimum number of method calls second. Each test in the resulting test suite consists of an initial construction statement to create a fresh instance of the smart contract, followed by one or more method calls that manipulate the state of the contract (see e.g. [here]()). Every branch in the [control dependency graph]() of the contract has one test dedicated to it.

If full branch coverage is achieved, running all the tests in the final test suite will guarantee that each branch of the smart contract is executed at least once, the user can then manually check to see if the results of the method calls match the expected behaviour to ensure proper testing. Otherwise, the user can check which branch is not covered and see if this branch can be covered manually (or if the code needs to be adapted).

## Quickstart
The easiest way to try out the SolAR is to download the dynamosadocker.tar and or fuzzerdocker.tar files from <a href="https://drive.google.com/drive/folders/1qAxzToqqCNkGBWFmDPC_O03BVCLDHbDX?usp=sharing">Google drive.</a>

These can be used in conjunction with docker using the commands:

```
docker load < fuzzerdocker.tar
docker load < dynamosadocker.tar

docker run -it fuzzer:1.2.0
docker run -it dynamosa:1.2.0
```

The file structure in the docker image is the same as the <a href="https://github.com/AGSolT/SolAR/tree/master/DynaMOSA">DynaMOSA</a> and <a href="https://github.com/AGSolT/SolAR/tree/master/Fuzzer">Fuzzer</a> folders in this git repository. To generate tests for a smart contract, simply copy the relevant smart contract folder from the SmartContracts/RWContracts folder to the SmartContracts/BatchContracts folder and run:

```
./Generate_Tests.sh
```

The configuration options for SolAR can be changed in the <a href="https://github.com/AGSolT/SolAR/blob/master/DynaMOSA/SolMOSA/Config.ini"> Config.ini</a> file. And the relevant options to be changed can be found either in table 3 of the paper, or by quickly looking at the <a href="https://github.com/AGSolT/SolAR/blob/master/Tracklist">Tracklist</a>.

## Running Locally
If you want to download the tool and play with the code locally, simply:

1. Download the code in this repository.
2. Set up and activate an [environment](https://docs.python.org/3/tutorial/venv.html) with python 3.7 (e.g., following [these](https://stackoverflow.com/questions/70422866/how-to-create-a-venv-with-a-different-python-version) instructions). Newer versions of python will be tested in the future.
3. Navigate to the folder you downloaded in step 1 and install the required python packages by running `pip install -r requirements.txt`.
4. Ensure that the all the required bash-scripts ([global], [dynamosa], [fuzzer]) are executable
5. You're ready to go! Follow the instructions below to start testing.

## Generating test suites for a smart contract.
SolAR runs in a unix-like terminal and requires a locally running Ethereum blockchain. We recommend the [ganache-cli]() implementation, which can be run from the terminal. If you have installed ganache-cli, you can run it yourself, or SolAR can start an instance in the background using [GNU-screen](), which is also what happens in the docker files. Nevertheless, for local test we recommend running your own instance in another terminal window with `ganache-cli` so you can see the interaction.

In order to generate tests for your smart contract, you should create a folder with your smart contract's name and point SolAR to this directory. The path to the directory is stored in the Config.ini files, which can be found [here]() for DynaMOSA, and [here]() for the Fuzzer. If you want, you can put multiple such folders in this directory, and SolAR will generate test suites for all of them.

The folders of your smart contracts should have a similar structure to the examples you can find in [RWContracts](). In particular, the tool expects an [ABI](), at `[SMART_CONTRACT_NAME]/build/contracts/[SMART_CONTRACT_NAME].json` for building the Control Dependency Graph, and the solidity contract itself at `[SMART_CONTRACT_NAME]/contracts/[[SMART_CONTRACT_NAME].sol` for scraping hardcoded values from the smart contract. SolAR works best with smart contracts that have been compiled with the [Truffle Suite](), which also ensures this structure automatically.

Once you've added your smart contracts in the right location, navigate to the main folder in your terminal
and execute [Generate_Tests.sh]() (don't forget to make this, the [dynamosa script]() and the [fuzzer script]() [executable]()). The script will provide you with prompts to run you through the execution of the tool.

Once SolAR is finished generating test suites, you can find the resulting test suites, as well as some stasticis, in the [Rapports Folder]().