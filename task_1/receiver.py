import socket
import pickle
from packet import Packet, PacketTypes, PacketCreator, File


class Receiver:

    def __init__(self, ip_src, port_src):
        self.ip_src = ip_src
        self.ip_dst = "127.0.0.1"
        self.port_src = port_src

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

    def receive_file(self, file_path):
        try:
            # Create UDP socket
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.bind((self.ip_dst, self.port_src))

            file = File()
            print(f"Waiting for data on port {self.port_src}...")

            total = 1
            received = 0

            while True:
                # Receive data along with sender's address
                serialized_packet, sender_address = udp_socket.recvfrom(1024)

                # Deserialize the Packet object using pickle
                received_packet = pickle.loads(serialized_packet)

                # print(f"Received packet from {sender_address}: {received_packet.__dict__}")

                pack = PacketCreator.parse_received(received_packet.__dict__)

                if pack.packet_type == PacketTypes.name:
                    file = File(pack.data)
                if pack.packet_type == PacketTypes.start:
                    file.set_length(pack.length)
                    total = pack.length
                if pack.packet_type == PacketTypes.data:
                    file.add_data(pack.data)
                    received += pack.length
                if pack.packet_type == PacketTypes.stop:
                    file.save_file()

                print("received {}%".format((received / total * 100).__round__(2)))

        except Exception as e:
            print(f"Error receiving data: {e}")
        finally:
            udp_socket.close()


if __name__ == "__main__":
    received_file_path = "path/to/save/received/file.txt"
    listening_port = 5000
    local_ip = Receiver.get_local_ip()
    if local_ip:
        receiver = Receiver(local_ip, listening_port)
        receiver.receive_file(received_file_path)
