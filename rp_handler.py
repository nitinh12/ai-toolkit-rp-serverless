import runpod
import subprocess
import os

def handler(event):
    try:
        # Explore the container structure
        commands = [
            "find /app -name '*.py' -type f | head -20",
            "find /workspace -name '*.py' -type f | head -20", 
            "find / -name 'run.py' -type f 2>/dev/null | head -10",
            "find / -name '*toolkit*' -type d 2>/dev/null | head -10",
            "ls -la /app/",
            "ls -la /workspace/",
            "which python",
            "python --version",
            "pip list | grep -i toolkit"
        ]
        
        results = {}
        for cmd in commands:
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                results[cmd] = {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }
            except Exception as e:
                results[cmd] = {"error": str(e)}
        
        return {
            "status": "diagnostic",
            "results": results
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e)
        }

if __name__ == '__main__':
    runpod.serverless.start({'handler': handler})
