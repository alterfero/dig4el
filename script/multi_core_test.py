import multiprocessing
import math

def cpu_bound_task(x):
    return math.factorial(300000)

if __name__ == '__main__':
    with multiprocessing.Pool() as pool:
        pool.map(cpu_bound_task, range(multiprocessing.cpu_count() * 5))

