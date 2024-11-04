from utils.data_preprocess import timed_function
import time

# 示例函数
def long_running_function(n):
    print(f"Starting a long-running function for {n} seconds...")
    time.sleep(n)
    print("Function completed.")
    return "Success"

def alter_func(n):
    print("Run alter func Function completed.")
    return "Success"

# 调用函数并设置超时时间
result = timed_function(long_running_function, alter_func, 10, timeout=5)
print("Result:", result)

