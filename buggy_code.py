import os
import numpy as np

def process_user_data(username, password):
    # 1. FIXED SECURITY RISK: Sourcing credentials from environment variables securely
    admin_user = os.environ.get("ADMIN_USERNAME", "admin")
    admin_password = os.environ.get("ADMIN_PASSWORD") # Kept safe outside of version control
    
    if not admin_password:
        print("System Alert: ADMIN_PASSWORD environment variable is not configured.")
        return False

    if username == admin_user and password == admin_password:
        print("Access Granted")
    else:
        print("Access Denied")
        return False

    # 2. FIXED PERFORMANCE BOTTLENECK: Eliminated 10-million loop appends using NumPy vectorization
    # This allocates memory contiguously and runs entirely in optimized C under the hood
    print("Processing computational arrays...")
    
    i_indices = np.arange(10000)[:, None]  # Column vector (10000, 1)
    j_indices = np.arange(1000)            # Row vector (1000,)
    
    # Broadcast multiplication computes all 10,000,000 products instantaneously
    data_matrix = i_indices * j_indices
    
    # Flatten back into a regular 1D python list to maintain matching signature
    return data_matrix.flatten().tolist()
