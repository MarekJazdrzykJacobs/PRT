from datetime import datetime

def measure_speed(func):

    """
    The method allows to measure speed of input func.
    It must be used as python decorator.

    :parameter
        func: (python method): method to be measured

    :returns
        wrapper (python method): modified func
    """

    def wrapper(*args, **kwargs):
        start = datetime.now()
        result = func(*args, **kwargs)
        stop = datetime.now()

        print('{0}:  {1}'.format(func.__name__, (stop - start).total_seconds()))
        return result
    return wrapper

