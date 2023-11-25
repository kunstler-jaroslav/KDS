from enum import Enum


class PacketTypes(Enum):
    data = 0
    start = 1
    stop = 2
    name = 3


class Packet:

    def __init__(self, packet_type, length, data):
        self.packet_type = packet_type
        self.length = length
        self.data = data


class PacketCreator:

    @staticmethod
    def start_packet(data):
        pack = Packet(PacketTypes.start, len(data), None)
        return pack

    @staticmethod
    def stop_packet():
        pack = Packet(PacketTypes.stop, 0, None)
        return pack

    @staticmethod
    def data_packet(data):
        pack = Packet(PacketTypes.data, len(data), data)
        return pack

    @staticmethod
    def name_packet(data):
        pack = Packet(PacketTypes.name, len(data), data)
        return pack

    @staticmethod
    def __get_packet_type_by_number(number):
        for packet_type in PacketTypes:
            if packet_type.value == number:
                return packet_type
        raise ValueError(f"No matching PacketType for number {number}")

    @staticmethod
    def parse_received(dictionary):
        pack = Packet(packet_type=dictionary['packet_type'], length=dictionary['length'], data=dictionary['data'])
        return pack


class File:

    def __init__(self, name="no_name"):
        self.name = name
        self.length = None
        self.data = b""

    def set_length(self, length):
        self.length = length

    def add_data(self, data):
        self.data = self.data + data

    def save_file(self):
        if len(self.data) == self.length:
            with open(self.name, 'wb') as file:
                file.write(self.data)
                file.close()
            print("File saved successfully")
        else:
            print("Error detected, repeat the process")
