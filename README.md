# AGSolT2021Submission
Online appendix for the AGSolT paper submitted to the joural of Software Testing, Verification & Reliability, the paper is currenlty available on <a href="https://arxiv.org/abs/2102.08864">arXiv</a>.

The test suites that were generated as part of the experiment for the paper can be found in the Results function and the code for the DynaMOSA and Fuzzer approach can be found in the corresponding folders.

The easiest way to try out the tool is to download the dynamosadocker.tar and or fuzzerdocker.tar files from <a href="https://drive.google.com/drive/folders/1qAxzToqqCNkGBWFmDPC_O03BVCLDHbDX?usp=sharing">Google drive.</a>

These can be used in conjunction with docker using the commands:

```
docker load < fuzzerdocker.tar
docker load < dynamosadocker.tar

docker run -it fuzzer:1.1.8
docker run -it dynamosa:1.1.8
```

The file structure in the docker image is the same as the <a href="https://github.com/AGSolT/AGSolT2021Submission/tree/master/DynaMOSA">DynaMOSA</a> and <a href="https://github.com/AGSolT/AGSolT2021Submission/tree/master/Fuzzer">Fuzzer</a> folders in this git repository. To generate tests for a smart contract, simply copy the relevant smart contract folder from the SmartContracts/RWContracts folder to the SmartContracts/BatchContracts folder and run:

```
./Generate_Tests.sh
```

The configuration options for AGSolT can be changed in the <a href="https://github.com/AGSolT/AGSolT2021Submission/blob/master/DynaMOSA/SolMOSA/Config.ini"> Config.ini</a> file. And the relevant options to be changed can be found either in table 3 of the paper, or by quickly looking at the <a href="https://github.com/AGSolT/AGSolT2021Submission/blob/master/Tracklist">Tracklist</a>.
