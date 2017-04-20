ps -ef | grep 'pirate\|quartermaster' | awk '{print $2}' | xargs kill -9
python -m py_compile *.py && ./pirate.py --spawnqm
