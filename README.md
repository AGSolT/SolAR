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

## Options and hyperparameters.
Hyperparameters are currently stored separately for the two algorithms in a Config.ini file which can be found [here]() for DynaMOSA, and [here]() for the fuzzer. They come in four categories, and are explained below.

#### CFG
These parameters are used by the [CDG.py]() component to generate control-flow and control dependency graphs.

- **Ignorefiles**: A list of ABI's that should be ignored when generating control flow graphs. Useful when your contract has dependencies such as libraries that are needed when constructing a new instance of the contract.
- **Predicates**: The predicates that can dominate a branch, these should generally not be changed.
- **ignoreFallback**: Tells the CDG component to exclude the fallback function from the control-dependency graph.

#### Blockchain
Parameters that are related to the local blockchain environment that SolAR interacts with. If you want to make other changes to your blockchain (e.g., increase or decrease the amount of Solidity per account, or deploy contracts that your contract can call) you should do those when launching the Ethereum client.
- **ETH_port**: the port where the local blockchain client is exposed.

#### Parameters
These are the main paremeters that can configure the DynaMOSA and Fuzzer algorithms. For more information on the DynaMOSA-specific parameters, we refer to the original [DynaMOSA paper]().
- **max_accounts**: The number of different accounts that are used to call methods in the smart contract. This should never be higher than the number of accounts that are on the blockchain. 
- **max_method_calls**: The maximum number of method calls in a single test in the test suite. Larger numbers theoretically allow for more complex behaviour but significantly affect runtime.
- **min_method_calls**: The minimum number of method calls in a single test in the test suite. Can be useful if you know certain branches can only be reached with a specific number of method calls.
- **maxArrayLength**: The maximum length of an array when generating input values for method calls. Longer arrays theoretically allow for more complex behaviour but significantly affect runtime.
- **minArrayLength**: The minimum length of an array when generating input values for method calls.
- **population_size**: The number of tests that generated during each iteration of the DynaMOSA or Fuzzer algorithm. Greatly affects runtime.
- **deploying_accounts**: A list of accounts that will always be used when constructing the smart contract. Useful if you want a specific account to always be the owner (e.g., when hardcoded).
- **tournament_size**: The size of the tournament used for to generate offspring in the DynaMOSA algorithm.
- **crossover_probability**: The probability of crossover when generating offspring in the DynaMOSA algorithm.
- **remove_probability**: The probability of removing when generating offspring in the DynaMOSA algorithm.
- **change_probability**: The probability of changing when generating offspring in the DynaMOSA algorithm.
- **insert_probability**: The probability of inserting when generating offspring in the DynaMOSA algorithm.
- **search_budget**: The amount of times SolAR will go through a full loop of generating new test cases if it doesn't achieve full branch coverage. If this is set to N; N+1 suites will be generated. Greatly affects runtime.
- **execution_times**: The number of optimal test suites to generate. Extremely bad for increasing runtime, mostly useful when conducting experiments.
- **passBlocks**: If set to True, test cases will include a special passBlocks method, which mines a couple of empty blocks and does nothing else. This is useful when contract functionality depends on the block number.
- **passTime**: If set to True, test cases will include a special passTime method, which artificially sets the clock of the blockchain a passTimeTime amount of time into the future. This is useful when contract funcitonality depends on the blockchain time.
- **passTimeTime**: The amount of time to set the blockchain into the future with the special passTime method.
- **standardPassTimeTime**: Fallback if no passTimeTime is specified.
- **memory_efficient**: Experimental parameter that was used when running experiments in containers where memory was an issue.
- **zeroAddress**: When set to true allows the special [zero address]() to be passed as an input variable to method calls.
- **maxWei**: The maximum amount of Wei that can be passed along with a method call.
- **IgnoreFunctions**: A list of methods that should not be called by the test suites.
- **ignoreStateVariables**: When set to true, does not call state variables.
- **nonExistantAccount**: A valid account hash that need not exist on the local blockchain environment. Useful for testing functionality that relies on non-existant accounts.

#### Files
Parameters surrounding the files that are used and created by SolAR.

- **accounts_file_location**: The location where the accounts in the local blockchain environment are stored.
- **rapports_folder**: The directory where the output of SolAR is saved to.
- **SmartContract_folder**: The folder where the smart contracts that are to be tested are stored.