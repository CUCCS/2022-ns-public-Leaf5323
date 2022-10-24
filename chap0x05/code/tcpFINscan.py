import scapy.layers.inet as sli
import scapy.sendrecv as ss
from sys import argv

def createFINpacket(destinationIP,destinationPort):
    packet=sli.IP(dst=destinationIP)/sli.TCP(dport=int(destinationPort),flags="F")
    return packet

def tcpFINscan(targetIP,targetPort):
    print("⫸ Sending FIN packet...")
    FINpacket=createFINpacket(targetIP,targetPort)
    gotAnswer=ss.sr1(FINpacket,timeout=10)
    if not gotAnswer:
        print("⫸ Port "+targetPort+": Open or Filtered")
    #elif gotAnswer.getlayer(sli.TCP).flags=="R": #这里有点为了判定而判定的意思，其实直接用else就行的
    else:
        print("⫸ Port "+targetPort+": Closed")

if __name__=='__main__':
    if len(argv)<3:
        print("ATTENTION: Super User Privilege required!!!")
        print("Usage: python tcpFINscan.py [target IP] [target Port]")
    else:
        tcpFINscan(targetIP=argv[1],targetPort=argv[2])