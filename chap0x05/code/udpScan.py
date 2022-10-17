import scapy.layers.inet as sli
import scapy.sendrecv as ss
from sys import argv

def createUDPpacket(destinationIP,destinationPort):
    packet=sli.IP(dst=destinationIP)/sli.UDP(dport=int(destinationPort))
    return packet

def UDPscan(targetIP,targetPort):
    print("⫸ Sending UDP packet...")
    UDPpacket=createUDPpacket(targetIP,targetPort)
    gotAnswer=ss.sr1(UDPpacket,timeout=10)
    if not gotAnswer:
        print("⫸ Port "+targetPort+": Open or Filtered")
    else:
        print("⫸ Port "+targetPort+": Closed")

if __name__ == '__main__':
    if len(argv)<3:
        print("ATTENTION: Super User Privilege required!!!")
        print("Usage: python udpScan.py [target IP] [target Port]")
    else:
        UDPscan(targetIP=argv[1],targetPort=argv[2])