'''
Created on Oct 5, 2012

@author: zoltanp
'''
import sys

def main():
    filename = sys.argv[1]
    
    data = []
    output = []
    
    for line in open(filename,"r"):
        if line[0] == "#":
            continue
        parts = line.split()
        time = parts[0]
        if parts[0] != "":
            power = parts[2]
            if not power:
                data.append(time)
            data.append(power)
        else:
            # new block
            output.append(data)
            print data
            data = []
    print "out:"
    print output


main()