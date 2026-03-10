

def iterable(obj):
    ''' test if object is iterable '''
    try:
        if isinstance(obj, str): return False
        iter(obj)
        return True
    except TypeError:
        return False

def diff(val1, val2):
    ''' get difference between numbers '''
    return max(val1, val2)- min(val1, val2)

def set_list_attr(l, name, val):
    ''' set an attribute on an object or list of objects'''
    if not iterable(l):
        setattr(l, name, val)
    else:
        for i in l: setattr(i, name, val)

def flatten(l):
    '''flatten a list by adding all items'''
    if not iterable(l): return l
    flat = l[0]
    for i in l[1:]:
        flat += i
    return flat

def write_file(data, filename):
    ''' write bytes to file '''
    print("  writing %s bytes to %s" %(len(data), filename))
    with open(filename, 'wb') as file_h:
        file_h.write(data)

class UnbufferedStdOut(object):
    '''Override to allow unbufferred std out to work with | tee'''
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        '''override'''
        self.stream.write(data)
        self.stream.flush()
    def writelines(self, datas):
        '''override'''
        self.stream.writelines(datas)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)
