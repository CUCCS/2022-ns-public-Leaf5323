import scapy.layers.inet as sli
import scapy.sendrecv as ss
from sys import argv

def createXmasPacket(destinationIP,destinationPort):
    packet=sli.IP(dst=destinationIP)/sli.TCP(dport=int(destinationPort),flags="FPU")
    return packet

def tcpXmasScan(targetIP,targetPort):
    print("⫸ Sending Xmas packet...")
    XmasPacket=createXmasPacket(targetIP,targetPort)
    gotAnswer=ss.sr1(XmasPacket,timeout=10)
    if not gotAnswer:
        print("⫸ Port "+targetPort+": Open or Filtered")
    #elif gotAnswer.getlayer(sli.TCP).flags=="R": #这里有点为了判定而判定的意思，其实直接用else就行的
    else:
        print("⫸ Port "+targetPort+": Closed")

if __name__=='__main__':
    if len(argv)<3:
        print("ATTENTION: Super User Privilege required!!!")
        print("Usage: python tcpXmasScan.py [target IP] [target Port]")
    else:
        tcpXmasScan(targetIP=argv[1],targetPort=argv[2])