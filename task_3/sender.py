# Task 3
import socket
import pickle
import time

from packet import Packet, PacketTypes, PacketCreator
import os


class Sender:

    def __init__(self, ip_src, port_src, ip_dst, port_dst, window_size):
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

        self.window_size = window_size

    def check_ack(self):
        try:
            ack, _ = self.s_rec.recvfrom(1024)
            CRC_ack, serialized_ack = ack[:4], ack[4:]
            if CRC_ack != PacketCreator.get_CRC(serialized_ack):
                print("Ack CRC mismatch")
                return True, []
                # Deserialize Ack packet sent from receiver:
            received_ack = pickle.loads(serialized_ack)
            pack = PacketCreator.parse_received(received_ack.__dict__)
            if pack.packet_type == PacketTypes.nack:
                print("Received negative acknowledgement, sending packet again..")
                return True, []
            if pack.packet_type == PacketTypes.ack:
                return True, pack.data
        except socket.timeout:
            print("Timeout. Sending packet again.")
            return True, []

    def __send_packet(self, packet, id):
        try:
            # Serialize the Packet object using pickle
            serialized_packet = pickle.dumps(packet)
            crc = PacketCreator.get_CRC(serialized_packet)
            hexdump = id.to_bytes(2, byteorder='big')
            id = hexdump.rjust(2, b'0')
            # print("Serialized packet:", serialized_packet)
            # print("Crc:", crc)
            # print("{} sent to {}:{}".format(len(crc + id + serialized_packet), self.ip_dst, self.port_dst))

            # Send the data to the receiver's address
            self.s_send.sendto(crc + id + serialized_packet, (self.ip_dst, self.port_dst))

        except Exception as e:
            print(f"Error sending packet: {e}")

    def __send_packet_block_with_ack(self, blocks, ids):
        success = []
        ack_check = False
        for i in range(len(blocks)):
            self.__send_packet(blocks[i], ids[i])
        while not ack_check or len(blocks) == 0:
            ack_check, success = self.check_ack()
        print(f"success {ack_check}: {success}")
        return success


    @staticmethod
    def __create_packets_to_send(data, file_name):
        packets_to_send_tmp = [PacketCreator.name_packet(file_name)]
        packets_to_send = []
        blocks = [data[i:i + 1024 - 109] for i in range(0, len(data), 1024 - 109)]
        for i in range(len(blocks)):
            packets_to_send.append(PacketCreator.data_packet(blocks[i]))
        packets_to_send.append(PacketCreator.hash_packet(data))
        packets_to_send.append(PacketCreator.stop_packet())
        packets_to_send_tmp.append(PacketCreator.start_packet(data, len(packets_to_send) + 2))
        packets_to_send = packets_to_send_tmp + packets_to_send
        ret = []
        for i in range(len(packets_to_send)):
            ret.append(i)
        return packets_to_send, ret

    def send_file(self, data, file_name):
        blocks, ids = self.__create_packets_to_send(data, file_name)
        to_send = blocks[0: self.window_size]
        ids_to_send = ids[0: self.window_size]
        while len(blocks) > 0:
            print(f"Sending: {ids_to_send}")
            sent_ids = self.__send_packet_block_with_ack(to_send, ids_to_send)
            for ind in sent_ids:
                try:
                    index = ids.index(ind)
                    blocks.pop(index)
                    ids.pop(index)
                except:
                    pass
            to_send = blocks[0:self.window_size]
            ids_to_send = ids[0: self.window_size]

    @staticmethod
    def file_to_byte_string(file_path):
        with open(file_path, 'rb') as file:
            byte_string = file.read()
        return byte_string


if __name__ == "__main__":
    # Sender
    local_ip = "127.0.0.1"
    local_port = 15001  # 50001

    # Receiver
    destination_ip = "127.0.0.1"
    destination_port = 14000

    bt = Sender.file_to_byte_string(r"C:\Users\kunst\Desktop\nature.jpg")
    fn = "nature.jpg"

    if local_ip:
        sender = Sender(local_ip, local_port, destination_ip, destination_port, 20)
        sender.send_file(bt, fn)
