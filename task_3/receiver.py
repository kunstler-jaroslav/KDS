# Task 3
import socket
import pickle
import time

from packet import Packet, PacketTypes, PacketCreator, File


class Receiver:

    def __init__(self, ip_src, port_src, port_dst):
        # Receiver
        self.ip_src = ip_src
        self.port_src = port_src

        print(ip_src)
        print(port_src)

        # Sender
        self.ip_dst = "192.168.43.196"
        self.port_dst = port_dst

        self.s_rec = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s_rec.bind((self.ip_src, self.port_src))

        self.s_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s_send.settimeout(10)
        self.s_rec.settimeout(100)
        self.last_rcvd_id = -1

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

    def send_ack(self):
        packet_to_send = PacketCreator.ack_packet()
        self.__send_packet(packet_to_send)

    def send_nack(self):
        packet_to_send = PacketCreator.nack_packet()
        self.__send_packet(packet_to_send)

    def receive_file(self):

        file = File()
        print(f"Waiting for data on port {self.port_src}...")

        total = 1
        received = 0

        while True:
            # Receive data along with sender's address

            serialized_packet, sender_address = self.s_rec.recvfrom(1024)
            CRC_received, id_received, serialized_packet = serialized_packet[:4], serialized_packet[
                                                                                  4:6], serialized_packet[6:]
            print("id:", id_received)
            # print(first_four_bytes)
            # print(PacketCreator.get_CRC(serialized_packet))
            if CRC_received != PacketCreator.get_CRC(serialized_packet):
                print("Received wrong CRC, sending nack")
                self.send_nack()

            else:
                print("new {}, last {}".format(id_received, self.last_rcvd_id))
                integer_value = int.from_bytes(id_received, byteorder='big')
                print("new {}, last {}".format(integer_value, self.last_rcvd_id))
                if integer_value == self.last_rcvd_id:
                    print("Received the same packet twice")
                    self.send_ack()

                else:

                    if self.ip_dst is None and sender_address is not None:
                        self.ip_dst = str(sender_address[0])

                    # Deserialize the Packet object using pickle
                    received_packet = pickle.loads(serialized_packet)

                    # print(f"Received packet from {sender_address}: {received_packet.__dict__}")

                    pack = PacketCreator.parse_received(received_packet.__dict__)

                    if pack.packet_type == PacketTypes.name:
                        file = File(pack.data)
                        self.send_ack()
                    if pack.packet_type == PacketTypes.start:
                        file.set_length(pack.length)
                        total = pack.length
                        self.send_ack()
                    if pack.packet_type == PacketTypes.data:
                        print("Saved data {}".format(id_received))
                        file.add_data(pack.data)
                        received += pack.length
                        self.send_ack()
                    if pack.packet_type == PacketTypes.hash:
                        hash_from_received = PacketCreator.get_hash(file.data)
                        assert pack.data == hash_from_received
                        print(hash_from_received)
                        print("Hash matches")
                        self.send_ack()
                    if pack.packet_type == PacketTypes.stop:
                        file.save_file()
                        self.send_ack()
                        received = 0

                    self.last_rcvd_id += 1
                    print("received {}%".format((received / total * 100).__round__(2)))


if __name__ == "__main__":
    local_ip = "192.168.43.195"
    listening_port = 15000

    # destination_ip = "127.0.0.1"  # Is unknown and set after first protocol
    destination_port = 14001  # 50001

    if local_ip:
        receiver = Receiver(local_ip, listening_port, destination_port)
        receiver.receive_file()
