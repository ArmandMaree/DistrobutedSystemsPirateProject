ps -ef | grep 'cluesolver\|quartermaster' | awk '{print $2}' | xargs kill -9

numcores="$(grep -c ^processor /proc/cpuinfo)"

echo "Spawning $numcores clue solvers."

for (( i = 0; i < $numcores; i++ )); do
	python cluesolver.py &
done

python quartermaster.py --first
