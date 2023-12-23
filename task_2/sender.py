import socket
import pickle
import time

from packet import Packet, PacketTypes, PacketCreator
import os


class Sender:

    def __init__(self, ip_src, port_src, ip_dst, port_dst):
        # Sender
        self.ip_src = ip_src
        self.port_src = port_src

        # Receiver
        self.ip_dst = ip_dst
        self.port_dst = port_dst

        self.s_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s_rec = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s_rec.bind((self.ip_src, self.port_src))
        self.s_send.settimeout(3)
        self.s_rec.settimeout(3)
        self.packet_id = 0

    @staticmethod
    def get_local_ip():

        try:
            # Create a socket object
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.1)

            # Connect to an external server (doesn't actually send data)
            s.connect(('10.255.255.255', 1))

            # Get the local IP address
            loc_ip = s.getsockname()[0]

            # Close the socket
            s.close()

            return str(loc_ip)
        except Exception as e:
            print(f"Error getting local IP address: {e}")
            return None

    def check_ack(self):
        try:
            ack, _ = self.s_rec.recvfrom(1024)
            CRC_ack, serialized_ack = ack[:4], ack[4:]
            if CRC_ack != PacketCreator.get_CRC(serialized_ack):
                print("Ack CRC mismatch")
                return False
                # Deserialize Ack packet sent from receiver:
            received_ack = pickle.loads(serialized_ack)
            pack = PacketCreator.parse_received(received_ack.__dict__)
            if pack.packet_type == PacketTypes.nack:
                print("Received negative acknowledgement, sending packet again..")
                return False
            if pack.packet_type == PacketTypes.ack:
                print("Ack received")
                self.packet_id += 1
                return True
        except socket.timeout:
            print("Timeout. Sending packet again.")
            return False

    def __send_packet_with_ack(self, packet):
        self.__send_packet(packet)
        while not self.check_ack():
            self.__send_packet(packet)

    def __send_packet(self, packet):
        try:
            # Serialize the Packet object using pickle
            serialized_packet = pickle.dumps(packet)
            crc = PacketCreator.get_CRC(serialized_packet)
            hexdump = self.packet_id.to_bytes(1, byteorder='big')
            id = hexdump.rjust(1, b'0')
            # print("Serialized packet:", serialized_packet)
            # print("Crc:", crc)
            print("{} sent to {}:{}".format(len(crc + id + serialized_packet), self.ip_dst, self.port_dst))

            # Send the data to the receiver's address
            self.s_send.sendto(crc + id + serialized_packet, (self.ip_dst, self.port_dst))

        except Exception as e:
            print(f"Error sending packet: {e}")

    def send_file(self, data, file_name):
        # Send name
        packet_to_send = PacketCreator.name_packet(file_name)
        self.__send_packet_with_ack(packet_to_send)
        # Send start
        packet_to_send = PacketCreator.start_packet(data)
        self.__send_packet_with_ack(packet_to_send)
        # Send file data
        blocks = [data[i:i + 1024 - 108] for i in range(0, len(data), 1024 - 108)]
        total = len(data)
        sent = 0
        for i in range(len(blocks)):
            packet_to_send = PacketCreator.data_packet(blocks[i])
            self.__send_packet_with_ack(packet_to_send)
            sent += len(blocks[i])
            print("sent {}%".format((sent / total * 100).__round__(2)), "packet id:", self.packet_id)
            os.system('cls' if os.name == 'nt' else 'clear')
        # Send file hash
        packet_to_send = PacketCreator.hash_packet(data)
        self.__send_packet_with_ack(packet_to_send)
        # Send stop
        packet_to_send = PacketCreator.stop_packet()
        self.__send_packet_with_ack(packet_to_send)

    @staticmethod
    def file_to_byte_string(file_path):
        with open(file_path, 'rb') as file:
            byte_string = file.read()
        return byte_string


if __name__ == "__main__":
    # Sender
    # local_ip = Sender.get_local_ip()
    local_ip = "127.0.0.1"
    local_port = 15001  # 50001

    # Receiver
    destination_ip = "127.0.0.1"
    destination_port = 14000

    bt = Sender.file_to_byte_string(r"/home/frederik/Desktop/dog.jpg")
    fn = "dog.jpg"

    if local_ip:
        sender = Sender(local_ip, local_port, destination_ip, destination_port)
        sender.send_file(bt, file_name=fn)
