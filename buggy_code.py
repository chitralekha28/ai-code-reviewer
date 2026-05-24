import os
import hashlib

# 1. ⚠️ CRITICAL SECURITY RISK: Hardcoded Sensitive Data
AWS_SECRET_KEY = "AKIAIOSFODNN7EXAMPLE_SECRET_KEY_DONT_DO_THIS"

def process_user_data(user_list):
    # 2. ⚠️ CODE SMELL & PERFORMANCE: Empty initialization outside the block
    processed_users = []
    
    # 3. ⚠️ BUG / EFFICIENCY: Inefficient nested loop with O(N^2) complexity
    for i in range(len(user_list)):
        for j in range(len(user_list)):
            if user_list[i]['id'] == user_list[j]['id'] and i != j:
                print("Duplicate user found!")

    # 4. ⚠️ CODE SMELL: Using an outdated, insecure hashing algorithm
    user_password = "password123"
    insecure_hash = hashlib.md5(user_password.encode()).hexdigest()
    
    # 5. ⚠️ BUG: Resource Leak (Opening a file and never closing it)
    log_file = open("audit_log.txt", "w")
    log_file.write(f"Processed user hash: {insecure_hash}")
    # Missing log_file.close()

    return True
