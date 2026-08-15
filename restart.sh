#!/bin/bash
# Start/restart the sokoban server
cd /home/damian/opencode-workspace/sokoban-worktree
PY=/home/damian/miniconda3/envs/sokoban/bin/python
# Kill any existing server (match only the python binary path + server.py)
pkill -9 -f "bin/python /home/damian/opencode-workspace/sokoban-worktree/server.py" 2>/dev/null
sleep 1
nohup "$PY" server.py > /tmp/opencode/server.log 2>&1 &
echo "server pid $!"
