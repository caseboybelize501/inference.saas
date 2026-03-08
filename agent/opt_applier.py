import subprocess

def apply_optimization(optimization_bundle):
    # Placeholder for applying optimization bundle to inference server
    print(f"Applying optimization: {optimization_bundle}")
    subprocess.run(['restart_inference_server', '--config', optimization_bundle])