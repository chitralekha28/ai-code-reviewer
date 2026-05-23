import os

def process_user_data(username, password):
    # SECURITY RISK: Hardcoded credentials
    if username == "admin" and password == "SuperSecret123!":
        print("Access Granted")

    # PERFORMANCE BOTTLENECK: Useless nested loops
    data_list = []
    for i in range(10000):
        for j in range(1000):
            data_list.append(i * j)

    return data_list
