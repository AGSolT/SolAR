# !/bin/bash
# Starts automatically generating test cases for the provided smart contracts

# Launch a ganache-client in another screen
screen -dmS ganache
screen -S ganache -p 0 -X stuff "ganache-cli\n"

# Start the DynaMOSA algorithm
cd DynaMOSA && python Main.py

# Close the ganache screen
screen -X -S ganache quit
