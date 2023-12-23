# Task 3
import socket
import pickle
import time

from packet import Packet, PacketTypes, PacketCreator, File


class Receiver:

    def __init__(self, ip_src, port_src, port_dst, window_size):
        # Receiver
        self.ip_src = ip_src
        self.port_src = port_src

        print(ip_src)
        print(port_src)

        # Sender
        self.ip_dst = "127.0.0.1"
        self.port_dst = port_dst

        self.s_rec = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s_rec.bind((self.ip_src, self.port_src))

        self.s_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s_send.settimeout(10)
        self.s_rec.settimeout(10)
        self.last_rcvd_id = -1
        self.highest_id = -10
        self.window_size = window_size

    def __send_packet(self, packet):
        try:
            # Serialize the Packet object using pickle
            serialized_packet = pickle.dumps(packet)
            crc = PacketCreator.get_CRC(serialized_packet)
            print("{} sent to {}:{}".format(len(crc + serialized_packet), self.ip_dst, self.port_dst))

            # Send the data to the receiver's address
            self.s_send.sendto(crc + serialized_packet, (self.ip_dst, self.port_dst))

        except Exception as e:
            print(f"Error sending packet: {e}")

    def send_ack(self, actual_block):
        ids = []
        for block in actual_block:
            ids.append(block[0])
        print(f"ack with ids: {ids}")
        packet_to_send = PacketCreator.ack_packet(ids)
        self.__send_packet(packet_to_send)

    def send_nack(self):
        packet_to_send = PacketCreator.nack_packet()
        self.__send_packet(packet_to_send)

    def get_highest_id(self, blocks):
        for block in blocks:
            if block[0] > self.highest_id:
                self.highest_id = block[0]

    def prepare_file_save(self, blocks):
        blocks = sorted(blocks, key=lambda x: x[0])
        file = File()
        for block in blocks:
            received_packet = pickle.loads(block[1])
            pack = PacketCreator.parse_received(received_packet.__dict__)
            if pack.packet_type == PacketTypes.name:
                file = File(pack.data)

            if pack.packet_type == PacketTypes.data:
                file.add_data(pack.data)

            if pack.packet_type == PacketTypes.hash:
                hash_from_received = PacketCreator.get_hash(file.data)
                assert pack.data == hash_from_received
                print(hash_from_received)
                print("Hash matches")

            if pack.packet_type == PacketTypes.stop:
                file.save_file()

    def receive_file(self):

        file = File()
        print(f"Waiting for data on port {self.port_src}...")

        all_blocks = []
        actual_block = []
        ids = []
        all_blocks_length = None

        runs = 0

        while True:
            # Receive data along with sender's address
            try:
                serialized_packet, sender_address = self.s_rec.recvfrom(1024)
                CRC_received, id_received, serialized_packet = serialized_packet[:4], serialized_packet[
                                                                                  4:6], serialized_packet[6:]

                self.s_rec.settimeout(0.2)
                if CRC_received != PacketCreator.get_CRC(serialized_packet):
                    print("Received wrong CRC, sending nack")

                else:

                    integer_value = int.from_bytes(id_received, byteorder='big')
                    actual_block.append([integer_value, serialized_packet])

                    # Deserialize the Packet object using pickle
                    received_packet = pickle.loads(serialized_packet)

                    pack = PacketCreator.parse_received(received_packet.__dict__)

                    if pack.packet_type == PacketTypes.start:
                        file.set_length(pack.length)
                        all_blocks_length = pack.data

            except Exception as E:
                pass
                print(f"No packet {E}")
            finally:
                runs += 1
                if runs >= self.window_size:
                    runs = 0
                    self.s_rec.settimeout(10)
                    for block in actual_block:
                        if block[0] not in ids:
                            print(f"block[0]: {block[0]} - {ids}")
                            all_blocks.append(block)
                            ids.append(block[0])
                    self.send_ack(actual_block)
                    print(f"length of all {len(all_blocks)}, should be {all_blocks_length}")
                    if all_blocks_length is not None and len(all_blocks) == all_blocks_length:
                        self.prepare_file_save(all_blocks)
                        break

                    actual_block = []


if __name__ == "__main__":
    local_ip = "127.0.0.1"
    listening_port = 15000

    # destination_ip = "127.0.0.1"  # Is unknown and set after first protocol
    destination_port = 14001  # 50001

    if local_ip:
        receiver = Receiver(local_ip, listening_port, destination_port, 20)
        receiver.receive_file()
