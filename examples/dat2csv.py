'''
Script to convert a .dat file to a .csv file
Usage: data2csv.ph input_dat_file output_csv_file

Format of the output file:
timestamp1, power1_channel_1, power1_channel_2, ... , power1_channel_N
timestamp2, power2_channel_1, power2_channel_2, ... , power2_channel_N
...
timestampM, powerM_channel_1, powerM_channel_2, ... , powerM_channel_N


'''
import sys

def main():
    if(len(sys.argv) != 3):
        print "usage: %s input_file output_file" % (sys.argv[0])
        return

    input_filename = sys.argv[1]
    output_filename = sys.argv[2]

    data = []
    output = []
    
    for line in open(input_filename,"r"):
        if line[0] == "#":
            continue
        parts = line.split()
        if len(parts) > 0 :
            time = parts[0]
            power = parts[2]
            if len(data) == 0:
                # in first element of a line, place a time-stamp
                data.append(time)
            data.append(power)
        else:
            # new block
            output.append(data)
            data = []


    fout = open(output_filename, "w")
    for line in output:
        fout.write(line[0])
        for value in line[1:]:
            fout.write( ", %s" % (value))
        fout.write("\n")
    fout.close()

main()
