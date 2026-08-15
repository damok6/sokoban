#!/bin/bash
# Start/restart the sokoban server
cd /home/damian/opencode-workspace/sokoban-worktree
PY=/home/damian/miniconda3/envs/sokoban/bin/python
# Kill any existing server on port 8000
if command -v fuser >/dev/null 2>&1; then
  fuser -k -9 8000/tcp 2>/dev/null
else
  pkill -9 -f "sokoban-worktree/server.py" 2>/dev/null
  pkill -9 -f "python server.py" 2>/dev/null
fi
sleep 1
nohup "$PY" server.py > /tmp/opencode/server.log 2>&1 &
echo "server pid $!"
