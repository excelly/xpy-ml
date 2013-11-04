from math import *
from copy import *
from random import random

def do_merge(arr, i1, i2, i3, buf):
    p1 = i1
    p2 = i2

    for p in range(i1, i3):
        if p1 < i2 and (p2 >= i3 or arr[p1] < arr[p2]):
            buf[p] = arr[p1]
            p1 += 1
        else:
            buf[p] = arr[p2]
            p2 +=1

arr = [int(random()*100) for ind in range(int(random()*20)+1)]
n = len(arr)
print 'length =', n
buf = [0]*n

for wnd in range(int(ceil(log(n,2)))):
    width = 2**wnd
    for ind in range(int(ceil(float(n)/width/2))):
        i1 = ind*width*2
        i2 = min(n, (ind*2+1)*width)
        i3 = min(n, (ind*2+2)*width)
        do_merge(arr, i1, i2, i3, buf)
    arr = copy(buf)

print arr
for ind in range(n-1):
	assert arr[ind] <= arr[ind+1], 'wrong result'
		