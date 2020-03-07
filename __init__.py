from mycroft import MycroftSkill, intent_file_handler, intent_handler
from adapt.intent import IntentBuilder
from mycroft.util import LOG

import time, math, socket, struct, time, netifaces, ipaddress, signal

class SkyQ(MycroftSkill):

    def __init__(self, ip):
        """ The __init__ method is called when the Skill is first constructed.
        It is often used to declare variables or perform setup actions, however
        it cannot utilise MycroftSkill methods as the class does not yet exist.
        """
        self.remoteControl = ip
        MycroftSkill.__init__(self)

    def initialize(self):
        """ 
        Perform any final setup needed for the skill here.
        This function is invoked after the skill is fully constructed and
        registered with the system. Intents will be registered and Skill
        settings will be available.
        """
        my_setting = self.settings.get('my_setting')

    @intent_file_handler('q.sky.intent')
    def handle_q_sky(self, message):
        self.speak_dialog('q.sky')

    @intent_file_handler('switch.to.intent')
    def handle_switch_to(self, message):
        spoken_num = message.data.get('number')
        self.log.debug('Numero inserito: ' + spoken_num)
        #self.remoteControl.press(spoken_num)
        self.speak_dialog('ok.intent')

    @intent_file_handler('button.intent')
    def handle_button(self, message):
        spoken_button = message.data.get('buttons')
        self.log.info(spoken_button)
        #self.remoteControl.press(spoken_button)
        self.speak_dialog('q.sky')

    def stop(self):
        pass


def create_skill():
    # Discover all sky q in the mycroft network
    #skyq_list = discover()
    # Let the user decide which sky q to control
    #self.remoteControl = sky_remote(str(skyq_list[0]))
    return SkyQ('0.0.0.0')


# Class used to control a sky q
class SkyRemote:
    commands={"power": 0, "select": 1, "backup": 2, "dismiss": 2, "channelup": 6, "channeldown": 7, "interactive": 8, "sidebar": 8, "help": 9, "services": 10, "search": 10, "tvguide": 11, "home": 11, "i": 14, "text": 15,  "up": 16, "down": 17, "left": 18, "right": 19, "red": 32, "green": 33, "yellow": 34, "blue": 35, 0: 48, 1: 49, 2: 50, 3: 51, 4: 52, 5: 53, 6: 54, 7: 55, 8: 56, 9: 57, "play": 64, "pause": 65, "stop": 66, "record": 67, "fastforward": 69, "rewind": 71, "boxoffice": 240, "sky": 241}
    connectTimeout = 1000

    def __init__(self, ip, port=49160):
        self.ip=ip
        self.port=port

    def press(self, sequence):
        if isinstance(sequence, list):
            for item in sequence:
                if item not in self.commands:
                    print('Invalid command: {}'.format(item))
                    break
                self.sendCommand(self.commands[item.casefold()])
                time.sleep(0.5)
        else:
            if sequence not in self.commands:
                print('Invalid command: {}'.format(sequence))
            else:
                self.sendCommand(self.commands[sequence])    

    def sendCommand(self, code):
        commandBytes = bytearray([4,1,0,0,0,0, int(math.floor(224 + (code/16))), code % 16])

        try:
            client=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as msg:
            print('Failed to create socket. Error code: %s , Error message : %s' % (str(msg[0]), msg[1]))
            return

        try:
            client.connect((self.ip, self.port))
        except:
            print("Failed to connect to client")
            return

        l=12
        timeout=time.time()+self.connectTimeout

        while 1:
            data=client.recv(1024)
            data=data

            if len(data)<24:
                client.sendall(data[0:l])
                l=1
            else:
                client.sendall(commandBytes)
                commandBytes[1]=0
                client.sendall(commandBytes)
                client.close()
                break

            if time.time() > timeout:
                print("timeout error")
                break


# Custom exception raised when a certain action takes longer than needed
class TimeOutException(Exception):
    pass

def alarm_handler(signum, frame):
    """
    Alarm handler used when getting fqdns from ips
    """
    raise TimeOutException()

def get_networks():
    """
    Function that return a list of valid network from the interfaces of the local host
    """

    # Return a list of network interfaces
    interfaces = netifaces.interfaces()

    # Networks to check
    networks = []
    
    for interface in interfaces:

        # Get the first interface that is not loopback, or br
        if 'lo' in interface:
            continue

        # Get a dictionary containing {'addr': , 'netmask': , 'broadcast': }
        ip_addr = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
        netmask = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['netmask']

        # Check if it is 127.0.0.1 or 127.0.1.1
        if ip_addr in ['127.0.0.1', '127.0.1.1']:
            continue

        # Obtain an object identifying the ip address
        iface = ipaddress.ip_interface(ip_addr + '/' + netmask)

        # Get the network ip
        # network = iface.network
        # Get only the address of the network (without the netmask)
        # network_address = iface.network.network_address
        # Check if it's a valid ip address/netmask

        # Create a network object
        network = ipaddress.IPv4Network(iface.network)

        # Check if it is private, if not continue with the next interface
        if not network.is_private:
            continue

        # Else insert it into the list to be returned
        networks.append(network)

    # After checking all the interfaces we can return a list of valid network
    return networks

def discover():
    """
    Function that search for a skyq in local network
    """
    # Get the ip address of the localhost
    networks = get_networks()

    # Lists of ip address for sky q found in the network
    skyqs = []

    # For every network in networks check if we can find a sky q
    for network in networks:
    
        # For every hosts in network look for a sky q
        for ip in list(network.hosts()):

            # Set signal alarm of 0.3 sec
            signal.signal(signal.SIGALRM, alarm_handler)
            signal.setitimer(signal.ITIMER_REAL, 0.3)

            # If the alarm send a signal then it means that this ip doesn't have a fqdn, so we continue with another one
            try:
                fqdn = socket.getfqdn(str(ip))
            except TimeOutException as ex:
                pass
            else:
                print(str(ip) + ' ' + fqdn)
                # If a fully qualified domain name contain skyq then we add its ip address to the list
                if 'skyq' in fqdn:
                    skyqs.append(ip)

            # Reset signal alarm
            signal.setitimer(signal.ITIMER_REAL, 0)

    # Finally we return the list containing the ip addresses of all the skyqs found in the network
    return skyqs

def write_discovered():
    """
    Function that write on file the discovered skyqs
    """

    try:
        # Open a file with write permission (overwrite)
        f = open("skyq-list.txt", "w")
    except OSError:
        print("Could not open/read file")
        return None
    
    # Create a string to be written on file
    string = ''
    # Get a list of skyq ips
    skyq_list = discover()
    # Iterate through that list to create a string
    for ip in skyq_list:
        string += str(ip) + ','
    # Delete the last ','
    string = string[:-1]
    # Write the string to the file
    f.write(string)
    # Close the file
    f.close()

def read_discovered():
    """
    Function that read from file the discovered skyqs
    """
    try:
        # Open a file with write permission (overwrite)
        f = open("skyq-list.txt", "r")
    except OSError:
        print("Could not open/read file")
        return None
        
    # Create a string with the content of the file
    string = f.read()
    # List with the ip addresses
    skyq_list = []
    # From that string create a list with ip addresses
    for ip in string.split(','):
        skyq_list.append(ip)
    # Close the file
    f.close()
    # Return the list
    return skyq_list

# How to create a sky remote:
#from sky_remote import SkyRemote
#remoteControl = sky_remote.SkyRemote('192.168.0.40')
## Just send a command
#remoteControl.press('power')
## Now send sequences of commands
#remoteControl.press(['channelup', 'record', 'select'])

#Sky Q (if firmware < 060):
#remoteControl = SkyRemote('192.168.0.40', SkyRemote.SKY_Q_LEGACY)


# All the buttons that can be pressed:
# sky power
# tvguide or home boxoffice services or search interactive or sidebar
# up down left right select
# channelup channeldown i
# backup or dismiss text help
# play pause rewind fastforward stop record
# red green yellow blue
# 0 1 2 3 4 5 6 7 8 9

if __name__ == '__main__':
    # If there aren't any skyqs listed in the file, then we start the discover process
    skyq_list = read_discovered()
    if skyq_list is None or not skyq_list:
        write_discovered()
        skyq_list = read_discovered()
    
    # Print out the list
    LOG.info(skyq_list)


