import socket
import pickle
import time

from packet import Packet, PacketTypes, PacketCreator
import os


class Sender:

    def __init__(self, ip_src, ip_dst, port_dst):
        self.ip_src = ip_src
        self.ip_dst = ip_dst
        self.port_dst = port_dst

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

    def __send_packet(self, packet):
        try:
            # Create a TCP socket
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Serialize the Packet object using pickle
            serialized_packet = pickle.dumps(packet)
            # print(len(serialized_packet))
            # print(serialized_packet)

            # Send the data to the receiver's address
            udp_socket.sendto(serialized_packet, (self.ip_dst, self.port_dst))

            udp_socket.close()
        except Exception as e:
            print(f"Error sending number: {e}")

    def send_file(self, data, file_name):
        # Send name
        packet_to_send = PacketCreator.name_packet(file_name)
        self.__send_packet(packet_to_send)
        # Send start
        packet_to_send = PacketCreator.start_packet(data)
        self.__send_packet(packet_to_send)
        # Send file data
        total = len(data)
        sent = 0
        blocks = [data[i:i + 1024-103] for i in range(0, len(data), 1024-103)]
        for i in range(len(blocks)):
            sent += 1024-103
            print("sent {}%".format((sent/total * 100).__round__(2)))
            packet_to_send = PacketCreator.data_packet(blocks[i])
            self.__send_packet(packet_to_send)
            time.sleep(0.00001)
        # Send stop
        packet_to_send = PacketCreator.stop_packet()
        self.__send_packet(packet_to_send)

    @staticmethod
    def file_to_byte_string(file_path):
        with open(file_path, 'rb') as file:
            byte_string = file.read()
        return byte_string


if __name__ == "__main__":
    bt = Sender.file_to_byte_string(r"C:\Users\kunst\Desktop\dog.jpg")
    destination_host = "10.0.0.223"
    destination_port = 5000
    local_ip = Sender.get_local_ip()
    print(local_ip)
    fn = "dog.jpg"
    if local_ip:
        sender = Sender(local_ip, destination_host, destination_port)
        sender.send_file(bt, file_name=fn)
