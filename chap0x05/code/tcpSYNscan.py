import scapy.layers.inet as sli
import scapy.sendrecv as ss
from sys import argv

def createSYNpacket(destinationIP,destinationPort):
    packet=sli.IP(dst=destinationIP)/sli.TCP(dport=int(destinationPort),flags="S")
    return packet

def createRSTpacket(destinationIP,destinationPort):
    packet=sli.IP(dst=destinationIP)/sli.TCP(dport=int(destinationPort),flags="R")
    return packet

def tcpSYNscan(targetIP,targetPort):
    print("⫸ Seding TCP SYN packet...")
    SYNpacket=createSYNpacket(destinationIP=targetIP,destinationPort=targetPort)
    gotAnswer=ss.sr1(SYNpacket,timeout=10)
    if not gotAnswer:
        print("⫸ Port "+targetPort+": Filtered")
    elif gotAnswer.getlayer(sli.TCP).flags=='RA':
        print("⫸ Port "+targetPort+": Closed")
    elif gotAnswer.getlayer(sli.TCP).flags=='SA':
        print("⫸ Port "+targetPort+": Open")
        print("⫸ Sending TCP RST packet...")
        RSTpacket=createRSTpacket(targetIP,targetPort)
        ss.send(RSTpacket) 

if __name__=='__main__':
    if len(argv)<3:
        print("ATTENTION: Super User Privilege required!!!")
        print("Usage: python tcpSYNscan.py [target IP] [target port]")
    else:
        tcpSYNscan(targetIP=argv[1],targetPort=argv[2])