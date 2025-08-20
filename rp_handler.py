import runpod
import subprocess
import json
import os
import logging

# Set up logging
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
        
        # Run the training process with longer timeout for training
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=7200)  # 2 hour timeout
        
        if result.returncode == 0:
            logger.info("Training completed successfully")
            return {
                "status": "completed",
                "message": "Training completed successfully",
                "output": result.stdout,
                "config_used": config_content
            }
        else:
            logger.error(f"Training failed with return code {result.returncode}")
            return {
                "status": "failed",
                "message": "Training failed",
                "error": result.stderr,
                "output": result.stdout
            }
            
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "message": "Training timed out after 2 hours"
        }
    except Exception as e:
        logger.error(f"Handler error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == '__main__':
    logger.info("Starting RunPod serverless handler...")
    runpod.serverless.start({'handler': handler})
