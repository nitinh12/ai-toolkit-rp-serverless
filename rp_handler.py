import runpod
import subprocess
import os

def handler(event):
    try:
        # Check network storage mounting
        commands = [
            "ls -la /",
            "ls -la /workspace/",
            "df -h",
            "mount | grep workspace",
            "find /workspace -type d | head -10",
            "ls -la /workspace/dataset/",
            "ls -la /workspace/lora-files/"
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
