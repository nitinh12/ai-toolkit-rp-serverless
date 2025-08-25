import runpod
import subprocess
import os
import glob
import threading
from supabase import create_client, Client

def init_supabase():
    """Initialize Supabase client"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    return create_client(url, key)

def download_training_images(supabase: Client, user_id: str, selected_images: list):
    """Download selected images from Supabase to container"""
    dataset_dir = '/tmp/dataset'
    os.makedirs(dataset_dir, exist_ok=True)
    
    bucket_name = "training-images"
    
    for image_path in selected_images:
        try:
            # Download image file
            filename = os.path.basename(image_path)
            local_image_path = os.path.join(dataset_dir, filename)
            
            response = supabase.storage.from_(bucket_name).download(image_path)
            with open(local_image_path, 'wb') as f:
                f.write(response)
            
            # Download corresponding caption file
            caption_path = image_path.replace('.jpg', '.txt').replace('.png', '.txt')
            caption_filename = filename.replace('.jpg', '.txt').replace('.png', '.txt')
            local_caption_path = os.path.join(dataset_dir, caption_filename)
            
            try:
                caption_response = supabase.storage.from_(bucket_name).download(caption_path)
                with open(local_caption_path, 'wb') as f:
                    f.write(caption_response)
            except Exception:
                # Create default caption if txt file doesn't exist
                with open(local_caption_path, 'w') as f:
                    f.write("a photo")
                    
        except Exception as e:
            print(f"Failed to download {image_path}: {e}")
    
    return dataset_dir

def upload_result_to_supabase(supabase: Client, local_path: str, user_id: str, training_name: str, file_type: str):
    """Upload training results to Supabase Storage"""
    bucket_name = "training-results"
    filename = os.path.basename(local_path)
    storage_path = f"{user_id}/{training_name}/{file_type}/{filename}"
    
    try:
        with open(local_path, 'rb') as f:
            supabase.storage.from_(bucket_name).upload(storage_path, f)
        
        url_response = supabase.storage.from_(bucket_name).get_public_url(storage_path)
        return url_response.get('publicUrl')
        
    except Exception as e:
        print(f"Failed to upload {local_path}: {e}")
        return None

def notify_website(callback_url: str, data: dict):
    """Notify website about new files"""
    try:
        import requests
        requests.post(callback_url, json=data, timeout=10)
    except Exception as e:
        print(f"Failed to notify website: {e}")

def handler(event):
    try:
        # Initialize Supabase
        supabase = init_supabase()
        
        # Extract parameters
        config_content = event['input'].get('config')
        training_name = event['input'].get('training_name')
        user_id = event['input'].get('user_id')
        selected_images = event['input'].get('selected_images', [])
        callback_url = event['input'].get('callback_url')
        
        print(f"Starting training for user {user_id} with {len(selected_images)} images")
        
        # Download selected training images
        dataset_dir = download_training_images(supabase, user_id, selected_images)
        
        # Update config to use downloaded dataset
        updated_config = config_content.replace(
            'folder_path: "/runpod-volume/dataset"',
            f'folder_path: "{dataset_dir}"'
        )
        
        # Create config file
        config_path = f'/tmp/{training_name}.yml'
        with open(config_path, 'w') as f:
            f.write(updated_config)
        
        # Start training
        cmd = ['python', '/app/ai-toolkit/run.py', config_path]
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            universal_newlines=True,
            bufsize=1
        )
        
        # Monitor and upload results in real-time
        uploaded_files = set()
        training_output = []
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                output_clean = output.strip()
                print(f"[TRAINING] {output_clean}")
                training_output.append(output_clean)
                
                # Check for new samples
                if "saved" in output_clean.lower() and "sample" in output_clean.lower():
                    sample_files = glob.glob('/tmp/samples/*.png')
                    for sample_file in sample_files:
                        if sample_file not in uploaded_files:
                            url = upload_result_to_supabase(supabase, sample_file, user_id, training_name, "samples")
                            if url and callback_url:
                                notify_website(callback_url, {
                                    'user_id': user_id,
                                    'training_name': training_name,
                                    'type': 'sample',
                                    'url': url,
                                    'filename': os.path.basename(sample_file)
                                })
                            uploaded_files.add(sample_file)
                
                # Check for checkpoints
                if "checkpoint" in output_clean.lower() and "saved" in output_clean.lower():
                    checkpoint_files = glob.glob('/tmp/*.safetensors')
                    for checkpoint_file in checkpoint_files:
                        if checkpoint_file not in uploaded_files:
                            url = upload_result_to_supabase(supabase, checkpoint_file, user_id, training_name, "checkpoints")
                            if url and callback_url:
                                notify_website(callback_url, {
                                    'user_id': user_id,
                                    'training_name': training_name,
                                    'type': 'checkpoint',
                                    'url': url,
                                    'filename': os.path.basename(checkpoint_file)
                                })
                            uploaded_files.add(checkpoint_file)
        
        return_code = process.poll()
        
        if return_code == 0:
            return {
                "status": "completed",
                "message": "Training completed successfully",
                "user_id": user_id,
                "training_name": training_name
            }
        else:
            return {
                "status": "failed",
                "message": "Training failed",
                "error": f"Process exited with code {return_code}",
                "output": "\n".join(training_output[-50:])
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == '__main__':
    runpod.serverless.start({'handler': handler})
