ps -ef | grep 'cluesolver\|quartermaster' | awk '{print $2}' | xargs kill -9

numcores="$(grep -c ^processor /proc/cpuinfo)"

echo "Spawning $numcores clue solvers."

for (( i = 0; i < $numcores; i++ )); do
	./cluesolver.py  --host "192.168.8.101" &
done

./quartermaster.py --first --host "192.168.8.101"
