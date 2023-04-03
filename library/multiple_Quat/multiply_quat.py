import math
import numpy as np
import sys

base=sys.argv[1]
out=sys.argv[2]
grid=int(sys.argv[3])

def q_mult(q1, q2):
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    y = w1 * y2 + y1 * w2 + z1 * x2 - x1 * z2
    z = w1 * z2 + z1 * w2 + x1 * y2 - y1 * x2
    return ([x, y, z, w])

base=np.loadtxt(base)
smallgrid=np.loadtxt("./scripts/smallGrid_%d"%grid)
#v=np.zeros(4,len((linesbase)*125))
v=[]

for orient in base:
    for dqt in smallgrid:
        v.append(q_mult(orient,dqt))
	
np.savetxt(out,v,fmt="%f")




