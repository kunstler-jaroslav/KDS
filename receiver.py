import socket
import pickle
import time

from packet import Packet, PacketTypes, PacketCreator, File


class Receiver:

    def __init__(self, ip_src, port_src, port_dst):
        # Receiver
        self.ip_src = ip_src
        self.port_src = port_src

        # Sender
        self.ip_dst = None
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
            print("{} sent to {}:{}".format(len(serialized_packet), self.ip_dst, self.port_dst))

            # Send the data to the receiver's address
            udp_socket.sendto(serialized_packet, (self.ip_dst, self.port_dst))

            udp_socket.close()

        except Exception as e:
            print(f"Error sending packet: {e}")

    def send_ack(self):
        packet_to_send = PacketCreator.ack_packet()
        self.__send_packet(packet_to_send)

    def receive_file(self):
        try:
            # Create UDP socket
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.bind((self.ip_src, self.port_src))

            file = File()
            print(f"Waiting for data on port {self.port_src}...")

            total = 1
            received = 0

            while True:
                # Receive data along with sender's address
                serialized_packet, sender_address = udp_socket.recvfrom(1024)

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
                    file.add_data(pack.data)
                    received += pack.length
                    self.send_ack()
                if pack.packet_type == PacketTypes.stop:
                    file.save_file()
                    self.send_ack()

                print("received {}%".format((received / total * 100).__round__(2)))

        except Exception as e:
            print(f"Error receiving data: {e}")
        finally:
            udp_socket.close()


if __name__ == "__main__":
    #local_ip = Receiver.get_local_ip()
    local_ip = "127.0.0.1"
    listening_port = 5000

    # destination_ip = "127.0.0.1"  # Is unknown and set after first protocol
    destination_port = 4999

    if local_ip:
        receiver = Receiver(local_ip, listening_port, destination_port)
        receiver.receive_file()
