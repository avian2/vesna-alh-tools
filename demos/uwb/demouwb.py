import vesna.alh
import uwbnode as uwb
import serial

if __name__ == "__main__":
    f =  serial.Serial("/dev/ttyUSB0", 921600, timeout=1)
    node = vesna.alh.ALHTerminal(f)

    uwbnode = uwb.UWBNode(node)

    while(True):
        print("NodeID: %s" % uwbnode.get_sensor_id())
        print("pending: %s" % uwbnode.check_pending_measurement())
        res = uwbnode.get_last_range_data()
        print(res['Range'])
        print(res['Node_ID'])

