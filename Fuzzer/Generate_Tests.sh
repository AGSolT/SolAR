# !/bin/bash
# Starts automatically generating test cases for the provided smart contracts

# Start the SolMOSA algorithm
cd FuzzerCode && python Main.py

# Close the ganache screen
screen -X -S ganache quit
