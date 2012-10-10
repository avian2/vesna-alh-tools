'''
Script to convert a .dat file to a .csv file
Usage: data2csv.ph input_dat_file output_csv_file

Format of the output file:
0         , frequency_1,      frequency_2,          , frequency_N
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
    freq_table = []
    trace_number = 0
    
    for line in open(input_filename,"r"):
        if line[0] == "#":
            continue
        parts = line.split()
        if len(parts) > 0 :
            time = parts[0]
            freq = parts[1]
            power = parts[2]
            if len(data) == 0:
                # in first element of a line, place a time-stamp
                data.append(time)
                trace_number += 1
            if trace_number == 1:
                freq_table.append(freq)
            data.append(power)
        else:
            # new block
            output.append(data)
            data = []


    fout = open(output_filename, "w")
    # frequency table header
    fout.write("0")
    for freq in freq_table:
        fout.write(", %s" % (freq))
    fout.write("\n")
    # power values
    for line in output:
        fout.write(line[0])
        for value in line[1:]:
            fout.write( ", %s" % (value))
        fout.write("\n")
    fout.close()

main()
