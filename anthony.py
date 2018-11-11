#!/usr/bin/python

import json
import socket
import logging
import binascii
import struct
import argparse
import random
import pdb
import time


class ServerMessageTypes(object):
    TEST = 0
    CREATETANK = 1
    DESPAWNTANK = 2
    FIRE = 3
    TOGGLEFORWARD = 4
    TOGGLEREVERSE = 5
    TOGGLELEFT = 6
    TOGGLERIGHT = 7
    TOGGLETURRETLEFT = 8
    TOGGLETURRETRIGHT = 9
    TURNTURRETTOHEADING = 10
    TURNTOHEADING = 11
    MOVEFORWARDDISTANCE = 12
    MOVEBACKWARSDISTANCE = 13
    STOPALL = 14
    STOPTURN = 15
    STOPMOVE = 16
    STOPTURRET = 17
    OBJECTUPDATE = 18
    HEALTHPICKUP = 19
    AMMOPICKUP = 20
    SNITCHPICKUP = 21
    DESTROYED = 22
    ENTEREDGOAL = 23
    KILL = 24
    SNITCHAPPEARED = 25
    GAMETIMEUPDATE = 26
    HITDETECTED = 27
    SUCCESSFULLHIT = 28

    strings = {
        TEST: "TEST",
        CREATETANK: "CREATETANK",
        DESPAWNTANK: "DESPAWNTANK",
        FIRE: "FIRE",
        TOGGLEFORWARD: "TOGGLEFORWARD",
        TOGGLEREVERSE: "TOGGLEREVERSE",
        TOGGLELEFT: "TOGGLELEFT",
        TOGGLERIGHT: "TOGGLERIGHT",
        TOGGLETURRETLEFT: "TOGGLETURRETLEFT",
        TOGGLETURRETRIGHT: "TOGGLETURRENTRIGHT",
        TURNTURRETTOHEADING: "TURNTURRETTOHEADING",
        TURNTOHEADING: "TURNTOHEADING",
        MOVEFORWARDDISTANCE: "MOVEFORWARDDISTANCE",
        MOVEBACKWARSDISTANCE: "MOVEBACKWARDSDISTANCE",
        STOPALL: "STOPALL",
        STOPTURN: "STOPTURN",
        STOPMOVE: "STOPMOVE",
        STOPTURRET: "STOPTURRET",
        OBJECTUPDATE: "OBJECTUPDATE",
        HEALTHPICKUP: "HEALTHPICKUP",
        AMMOPICKUP: "AMMOPICKUP",
        SNITCHPICKUP: "SNITCHPICKUP",
        DESTROYED: "DESTROYED",
        ENTEREDGOAL: "ENTEREDGOAL",
        KILL: "KILL",
        SNITCHAPPEARED: "SNITCHAPPEARED",
        GAMETIMEUPDATE: "GAMETIMEUPDATE",
        HITDETECTED: "HITDETECTED",
        SUCCESSFULLHIT: "SUCCESSFULLHIT"
    }

    def toString(self, id):
        if id in self.strings.keys():
            return self.strings[id]
        else:
            return "??UNKNOWN??"


class ServerComms(object):
    '''
    TCP comms handler
    
    Server protocol is simple:
    
    * 1st byte is the message type - see ServerMessageTypes
    * 2nd byte is the length in bytes of the payload (so max 255 byte payload)
    * 3rd byte onwards is the payload encoded in JSON
    '''
    ServerSocket = None
    MessageTypes = ServerMessageTypes()

    def __init__(self, hostname, port):
        self.ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ServerSocket.connect((hostname, port))

    def readMessage(self):
        '''
        Read a message from the server
        '''
        messageTypeRaw = self.ServerSocket.recv(1)
        messageLenRaw = self.ServerSocket.recv(1)
        messageType = struct.unpack('>B', messageTypeRaw)[0]
        messageLen = struct.unpack('>B', messageLenRaw)[0]

        if messageLen == 0:
            messageData = bytearray()
            messagePayload = {'messageType': messageType}
        else:
            messageData = self.ServerSocket.recv(messageLen)
            logging.debug("*** {}".format(messageData))
            messagePayload = json.loads(messageData.decode('utf-8'))
            messagePayload['messageType'] = messageType

        logging.debug('Turned message {} into type {} payload {}'.format(
            binascii.hexlify(messageData),
            self.MessageTypes.toString(messageType),
            messagePayload))
        return messagePayload

    def sendMessage(self, messageType=None, messagePayload=None):
        '''
        Send a message to the server
        '''
        message = bytearray()

        if messageType is not None:
            message.append(messageType)
        else:
            message.append(0)

        if messagePayload is not None:
            messageString = json.dumps(messagePayload)
            message.append(len(messageString))
            message.extend(str.encode(messageString))

        else:
            message.append(0)

        logging.debug('Turned message type {} payload {} into {}'.format(
            self.MessageTypes.toString(messageType),
            messagePayload,
            binascii.hexlify(message)))
        return self.ServerSocket.send(message)

class States(object):
    SCAN = 'SCAN'
    MOVE = 'MOVE'

# Parse command line args
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
parser.add_argument('-H', '--hostname', default='127.0.0.1', help='Hostname to connect to')
parser.add_argument('-p', '--port', default=8052, type=int, help='Port to connect to')
parser.add_argument('-n', '--name', default='RandomBot', help='Name of bot')
args = parser.parse_args()

# Set up console logging
if args.debug:
    logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.DEBUG)
else:
    logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)

# Connect to game server
GameServer = ServerComms(args.hostname, args.port)

class States(object):
    NOTHING = 'NOTHING'

def getCartesian(x, y, b):
    m = (b - 90) / 360
    c = y - m * x
    return m, c

def getHeading(x1, y1, x2, y2):
    heading = math.atan2(y2 - y1, x2 - x1)
    heading = math.degrees(heading)
    heading = math.fmod(heading - 360, 360)
    return abs(heading)

def calculateDistance(x1, y1, x2, y2):
    headingX = x2 - x1
    headingY = y2 - y1
    return math.sqrt((headingX * headingX) + (headingY * headingY))

def targetStill(enemy_x, enemy_y, me_x, me_y):
    return getHeading(enemy_x, enemy_y, me_x, me_y)

def targetStraight(enemy_x, enemy_y, me_x, me_y):
    a = enemy_x
    b = enemy_y
    c = me_x
    d = me_y
    b = info.myTank['Heading']

    m, k = getCartesian(enemy_x, enemy_y, b)

    speed_e = tankSpeed
    speed_b = projectileSpeed

    x = 0.0
    y = 0.0

    a = (m ** 2 + 1) * (speed_b - speed_e)
    b = speed_b * (-2 * c + 2 * m * k - 2 * m * d) - speed_e * (-2 * a + 2 * m * k - 2 * m * b)
    c = speed_b * (a ** 2 + k ** 2 - 2 * k * b + b ** 2) - speed_b * (a ** 2 + k ** 2 - 2 * k * d + d ** 2)

    x = quadratic(a, b, c)
    y = m * x + k
    return getHeading(x, y, me_x, me_y)


def quadratic(a, b, c):
    return -2*b + Math.sqrt(b**2 - 4*a*c)

def targetRight(enemy_x, enemy_y, me_x, me_y, p):
    x, y = p
    a = enemy_x
    b = enemy_y
    c = me_x
    d = me_y
    r = turnRadius

    F[0] = sqrt((x-a)**2 + (y-b)) / speed_bullet - (r * arccos(1 - (x-c)**2 - (y-d)**2) / (2 * r**2)) / speed_enemy
    F[1] = (x-a)**2 + (y-b)**2 - r**2
    enemy_x, enemy_y = equation(F)
    return getHeading(enemy_y, enemy_y, me_x, me_y)

def equation(F):
    zGuess = array([1,1])
    z = fsolve(equation, zGuess)
    return z


class Info(object):
    def __init__(self):
        self.myTank = None
        self.healthPickups = {}
        self.ammoPickups = {}
        self.snitch = None
        self.enemies = {}
        self.prevEnemies = {}

    def update(self, message):
        if message['messageType'] == ServerMessageTypes.OBJECTUPDATE:
            if message['Type'] == 'Tank':
                if message['Name'] == args.name:
                    self.myTank = message
                else:
                    if (message['Id'] in self.enemies):
                        self.prevEnemies[message['Id']] = self.enemies[message['Id']]
                    self.enemies[message['Id']] = message
            elif message['Type'] == 'HealthPickup':
                self.healthPickups[message['Id']] = message
            elif message['Type'] == 'AmmoPickup':
                self.ammoPickups[message['Id']] = message
            elif message['Type'] == 'Snitch':
                self.snitch = message
            else:
                print('Unrecognized message type:', message)

# Spawn our tank
logging.info("Creating tank with name '{}'".format(args.name))
GameServer.sendMessage(ServerMessageTypes.CREATETANK, {'Name': args.name})

maxHealth = 5
ammo = 10
waitTime = 50
info = Info()
tankSpeed = None
projectileSpeed = None
turnRadius = 5.7815

def tryShot():
    turretHeading = info.myTank["TurretHeading"]
    xm = info.myTank['X']
    ym = info.myTank['Y']
    for enemy in info.prevEnemies:
        x1 = info.prevEnemies[enemy]['X']
        y1 = info.prevEnemies[enemy]['Y']
        h1 = info.prevEnemies[enemy]['Heading']
        x2 = info.enemies[enemy]['X']
        y2 = info.enemies[enemy]['Y']
        h2 = info.enemies[enemy]['Heading']
        ht = None

        if (x1 == x2 and y1 == y2):
            ht = targetStill(x2, y2, xm, ym)
        elif (x1 != x2 or y1 != y2) and h1 == h2:
            ht = targetStraight(x2, y2, xm, ym)
        elif (x1 != x2 or y1 != y2) and h1 > h2:
            ht = targetRight(x2, y2, xm, ym)
        elif (x1 != x2 or y1 != y2) and h1 < h2:
            ht = targetRight(x2, y2, xm, ym)
        else:
            return
        if turretHeading == ht:
            GameServer.sendMessage(ServerMessageTypes.FIRE)

def Main():
    tes = 0
    x1 = 0
    x2 = 0
    t1 = 0
    t2 = 0

    while True:
        message = GameServer.readMessage()
        info.update(message)

        #GameServer.sendMessage(ServerMessageTypes.TOGGLETURRETRIGHT)
        #GameServer.sendMessage(ServerMessageTypes.TOGGLERIGHT)
        time.sleep(1)
        if tes == 0:
            t1 = time.time()
            x1 = info.myTank['X']
            y1 = info.myTank['Y']
            GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {'Amount':90})
            time.sleep(2)
            GameServer.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE, {'Amount':10})
            tes = 1
        x2 = info.myTank['X']
        y2 = info.myTank['Y']
        logging.info(x1)
        logging.info(x2)
        logging.info(y1)
        logging.info(y2)
        if x2 >= x1 + 9:
            t2 = time.time()
            print(t2-t1)

        #tryShot()


if __name__ == '__main__':
    Main()
