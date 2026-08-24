#!/bin/bash
echo "Recompiling CathedralOS..."
g++ pantry.cpp -o pantry -lraylib -lm -lpthread -ldl
echo "Done. Run ./pantry to initiate ritual."

