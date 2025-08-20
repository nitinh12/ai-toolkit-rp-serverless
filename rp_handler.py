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
        config_path = f'/app/config/{training_name}.yml'
        os.makedirs('/app/config', exist_ok=True)
        
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        logger.info(f"Config file created at {config_path}")
        
        # Run the training process using the AI Toolkit's run.py
        cmd = [
            'python', 
            '/app/run.py',
            config_path
        ]
        
        # Set environment variables if needed
        env = os.environ.copy()
        env['PYTHONPATH'] = '/app'
        
        logger.info("Starting training process...")
        
        # Run the training process
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
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
            
    except Exception as e:
        logger.error(f"Handler error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == '__main__':
    logger.info("Starting RunPod serverless handler...")
    runpod.serverless.start({'handler': handler})
