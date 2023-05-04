# !/bin/bash
# Starts automatically generating test cases for the provided smart contracts

python Initiate.py
read -p "Currently, two algorithmic approaches are supported: Press '1' to generate tests based on DynaMOSA, and '2' to generate tests based on Fuzzing.
" choice

if [ $choice = '1' ]; then
	cd DynaMOSA/SolMOSA && python Main.py
elif [ $choice = '2' ]; then
	cd Fuzzer/FuzzerCode && python Main.py
else
    echo "invalid choice!"
fi
# Start the SolMOSA algorithm
# cd SolMOSA && python Main.py

# Close the ganache screen
screen -X -S ganache quit
