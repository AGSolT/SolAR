# !/bin/bash
# Starts automatically generating test cases for the provided smart contracts

# Start the DynaMOSA algorithm
cd DynaMOSA && python Main.py

# Close the ganache screen
screen -X -S ganache quit
