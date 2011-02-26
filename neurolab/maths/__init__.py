def NaNs(shape):
    from numpy import ndarray, NaN
    array = ndarray(shape)
    array.fill(NaN)
    return array
