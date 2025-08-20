import runpod
import subprocess
import json
import os
import logging
import sys

# Set up logging to show in RunPod console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handler(event):
    """
    Handler function for RunPod Serverless using ostris/aitoolkit:latest
    """
    try:
        logger.info("Starting training job...")
        
        # Extract input parameters from the request
        input_data = event['input']
        
        # Get training parameters
        config_content = input_data.get('config')
        training_name = input_data.get('training_name', 'lora_training')
        
        if not config_content:
            return {
                "status": "error",
                "message": "No config provided"
            }
        
        # Create config file
        config_path = f'/tmp/{training_name}.yml'
        
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        logger.info(f"Config file created at {config_path}")
        
        # Create output directory if it doesn't exist
        os.makedirs('/runpod-volume/lora-files', exist_ok=True)
        
        # Initialize log file
        log_file_path = '/runpod-volume/lora-files/training.log'
        with open(log_file_path, 'w') as log_file:
            log_file.write(f"Training started: {training_name}\n")
            log_file.write(f"Config: {config_content[:200]}...\n")
            log_file.write("="*50 + "\n")
        
        # Use the correct AI Toolkit path
        cmd = [
            'python', 
            '/app/ai-toolkit/run.py',
            config_path
        ]
        
        # Set environment variables
        env = os.environ.copy()
        env['PYTHONPATH'] = '/app/ai-toolkit'
        
        logger.info(f"Starting training process with command: {' '.join(cmd)}")
        
        # Run the training process with real-time output streaming
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            universal_newlines=True,
            env=env,
            bufsize=1
        )
        
        # Stream output in real-time
        training_output = []
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                output_clean = output.strip()
                
                # Print to console so it shows in RunPod logs
                print(f"[TRAINING] {output_clean}")
                sys.stdout.flush()  # Force flush to show immediately
                
                # Save logs to network storage too
                with open(log_file_path, 'a') as log_file:
                    log_file.write(f"{output_clean}\n")
                
                training_output.append(output_clean)
        
        # Wait for process to complete
        return_code = process.poll()
        
        # Write final status to log file
        with open(log_file_path, 'a') as log_file:
            log_file.write("="*50 + "\n")
            log_file.write(f"Training completed with return code: {return_code}\n")
        
        if return_code == 0:
            logger.info("Training completed successfully")
            return {
                "status": "completed",
                "message": "Training completed successfully",
                "output": "\n".join(training_output[-50:]),  # Last 50 lines
                "log_file": log_file_path
            }
        else:
            logger.error(f"Training failed with return code {return_code}")
            return {
                "status": "failed",
                "message": "Training failed",
                "error": f"Process exited with code {return_code}",
                "output": "\n".join(training_output[-50:]),  # Last 50 lines
                "log_file": log_file_path
            }
            
    except Exception as e:
        logger.error(f"Handler error: {str(e)}")
        
        # Log the error to network storage too
        try:
            log_file_path = '/runpod-volume/lora-files/training.log'
            with open(log_file_path, 'a') as log_file:
                log_file.write(f"ERROR: {str(e)}\n")
        except:
            pass
            
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == '__main__':
    logger.info("Starting RunPod serverless handler...")
    runpod.serverless.start({'handler': handler})
