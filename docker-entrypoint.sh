#!/bin/bash
# Ensure Claude Code MCP config for ghidra-server is present

CLAUDE_JSON="$HOME/.claude.json"
PROJECT_PATH="/project/drol_re"

python3 -c "
import json, os

path = '$CLAUDE_JSON'
project = '$PROJECT_PATH'

if os.path.exists(path):
    with open(path) as f:
        d = json.load(f)
else:
    d = {}

projects = d.setdefault('projects', {})
proj = projects.setdefault(project, {})
mcp = proj.get('mcpServers', {})

if 'ghidra-server' not in mcp:
    mcp['ghidra-server'] = {
        'type': 'stdio',
        'command': 'python3',
        'args': [
            '/opt/ghidra_12.0.3_PUBLIC/bridge_mcp_ghidra.py',
            '--ghidra-server', 'http://host.docker.internal:8089'
        ],
        'env': {}
    }
    proj['mcpServers'] = mcp
    with open(path, 'w') as f:
        json.dump(d, f, indent=2)
    print('ghidra-server MCP configured')
else:
    print('ghidra-server MCP already configured')
"

exec "$@"
