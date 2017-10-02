import math
import numpy as np


def parseCIR2Complex(data):
    """make a list of strings with complex cir points
    ['2+3j','3+2j']
    """
    length = int(len(data) / 4)
    tempreal = None
    tempcpx = None
    cpx_data = []
    for x in range(length):
        tempreal = ((ord(data[(x * 4)])) << 8) + (ord(data[(x * 4) + 1]))
        # convert unsigned integer to signed integer
        if (tempreal & 0x8000):
            tempreal = -0x10000 + tempreal
        tempcpx = ((ord(data[(x * 4) + 2])) << 8) + (ord(data[(x * 4) + 3]))
        if (tempcpx & 0x8000):
            tempcpx = -0x10000 + tempcpx
        cpx_data.append(str(complex(tempreal, tempcpx)))

    return cpx_data

def signal_power(datadict, fp1, fp2, fp3, cir_power, prfr):
    """
        calculate vector of first path power and total signal power
    """
    # RCPE first path
    rcpe_fp = 10 * np.log10((np.power(fp1, 2) + np.power(fp2, 2) + np.power(fp3, 2)) / (np.power(datadict['RXPACC'], 2)))
    # RCPE
    if cir_power == 0.0:
        rcpe = rcpe_fp
    else:
        rcpe = 10 * np.log10((cir_power * math.pow(2, 17)) / (np.power(datadict['RXPACC'], 2)))

    # compensate for PRFR
    if int(prfr) == 16:
        rcpe = rcpe - 115.72
        rcpe_fp = rcpe_fp - 115.72
    else:
        rcpe = rcpe - 121.74
        rcpe_fp = rcpe_fp - 121.74

    return rcpe, rcpe_fp


def dataLineToDictionary(line):
    msg_dict = {'Node_ID': None, 'Destination_ID': None, 'Range': None, 'RSS': None,
                'RSS_FP': None, 'Noise_STDEV': None, 'Max_noise': None,
                'RXPACC': None, 'FP_index': None, 'CIR': None}

    # Node ID
    idx = line.find("SRC:")
    if idx >= 0:
        temp_data = line[( idx +4):( idx + 4 +16)]
        msg_dict['Node_ID'] = temp_data
    # Destination_ID
    idx = line.find("DEST:")
    if idx >= 0:
        temp_data = line[( idx +5):( idx + 16 +5)]
        msg_dict['Destination_ID'] = temp_data
    # Range
    idx = line.find("DIST:")
    if idx >= 0:
        temp_data = float(line[( idx +5):( idx + 5 +5)])
        msg_dict['Range'] = temp_data
    # FP_index
    idx = line.find("FP_INDEX:")
    if idx >= 0:
        temp_data = int(line[( idx +9):( idx + 9 +3)])
        msg_dict['FP_index'] = temp_data
    # FP_point1
    idx = line.find("FP_AMPL1:")
    if idx >= 0:
        temp_data = int(line[( idx +9):( idx + 9 +5)])
        fp1 = temp_data
    # FP_point2
    idx = line.find("FP_AMPL2:")
    if idx >= 0:
        temp_data = int(line[( idx +9):( idx + 9 +5)])
        fp2 = temp_data
    # FP_point3
    idx = line.find("FP_AMPL3:")
    if idx >= 0:
        temp_data = int(line[( idx +9):( idx + 9 +5)])
        fp3 = temp_data
    # Noise_STDEV
    idx = line.find("STD_NOISE:")
    if idx >= 0:
        temp_data = int(line[( idx +10):( idx + 10 +5)])
        msg_dict['Noise_STDEV'] = temp_data
    # CIR_power
    idx = line.find("CIR_PWR:")
    if idx >= 0:
        temp_data = int(line[( idx +8):( idx + 8 +5)])
        cir_power = temp_data
    # Max_noise
    idx = line.find("MAX_NOISE:")
    if idx >= 0:
        temp_data = int(line[( idx +10):( idx + 10 +5)])
        msg_dict['Max_noise'] = temp_data
    # RXPACC
    idx = line.find("RXPACC:")
    if idx >= 0:
        temp_data = int(line[( idx +7):( idx + 7 +5)])
        msg_dict['RXPACC'] = temp_data
    # PRFR
    idx = line.find("PRFR:")
    if idx >= 0:
        temp_data = int(line[( idx +5):( idx + 5 +2)])
        prfr = temp_data
    # RSS and RSS_FP values
    msg_dict['RSS'], msg_dict['RSS_FP'] = signal_power(msg_dict, fp1, fp2, fp3, cir_power, prfr)

    return msg_dict



class UWBNode:
    """
    ALH node abstracting an UWB node functionality

    :param alh: ALH implementation used to communicate with the node
    """
    def __init__(self, alh):
        self.alh = alh

    def get_sensor_id(self):
        """ read the ID of UWB node """
        response = self.alh.get("node_id")

        return int(response.content)

    def get_last_range_data(self):
        """ return measurements data """
        response = self.alh.get("measurement")
        data_str = str(response.content)
        data = dataLineToDictionary(data_str)
        idx = data_str.find("DATALEN{")
        if idx >= 0:
            #datalen = int(response[idx+8:idx+12])
            data['CIR'] = parseCIR2Complex(data_str[idx+14:-1])

        return data

    def check_pending_measurement(self):
        """ check if measurement data is ready for transfer """
        response = self.alh.get("pending")

        return int(response.content)
