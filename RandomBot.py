#!/usr/bin/python

import json
import socket
import logging
import binascii
import struct
import argparse
import time
import math
import random
import numpy as np
import tensorflow

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

# Parse command line args
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
parser.add_argument('-H', '--hostname', default='127.0.0.1', help='Hostname to connect to')
parser.add_argument('-p', '--port', default=8052, type=int, help='Port to connect to')
parser.add_argument('-n', '--name', default='RandomBot', help='Name of bot')
args = parser.parse_args()

"""
# Preparing training data (inputs-outputs)
training_inputs = tensorflow.placeholder(shape=[None, ], dtype=tensorflow.float32)
training_outputs = tensorflow.placeholder(shape=[None, 1], dtype=tensorflow.float32) #Desired outputs for each input

#Preparing neural network parameters (weights and bias) using TensorFlow Variables
weights = tensorflow.Variable(initial_value=[[.3], [.1], [.8]], dtype=tensorflow.float32)
bias = tensorflow.Variable(initial_value=[[1]], dtype=tensorflow.float32)

# Preparing inputs of the activation function
af_input = tensorflow.matmul(training_inputs, weights) + bias

# Activation function of the output layer neuron
predictions = tensorflow.nn.sigmoid(af_input)

# Measuring the prediction error of the network after being trained
prediction_error = tensorflow.reduce_sum(training_outputs - predictions)

# Minimizing the prediction error using gradient descent optimizer
train_op = tensorflow.train.GradientDescentOptimizer(learning_rate=0.05).minimize(prediction_error)

# Creating a TensorFlow Session
sess = tensorflow.Session()

# ializing the TensorFlow Variables (weights and bias)
sess.run(tensorflow.global_variables_initializer())
"""
# Set up console logging
if args.debug:
    logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.DEBUG)
else:
    logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)

# Connect to game server
GameServer = ServerComms(args.hostname, args.port)

# Spawn our tank
logging.info("Creating tank with name '{}'".format(args.name))
GameServer.sendMessage(ServerMessageTypes.CREATETANK, {'Name': args.name})

# Main loop - read game messages, ignore them and randomly perform actions
# server params
maxHealth = 5
maxAmmo = 10

# params
waitTime = 50  # wait n milliseconds to send a new message
memoryTime = 200
healthThresh = 2  # health threshold to transite state
ammoThresh = 0  # ammo threshold to transite state
expectedDist = 17  # expected distance to the enemy
headingErrorMove = 10  # tolerable angle error for turning before moving
headingErrorFire = 8  # tolerable angle error for turning before firing
allowedStationaryTime = 200  # allowed stationary time before having to move again (to avoid attack)

# vars
stationaryTime = 0

def getHeading(x1, y1, x2, y2):
    heading = math.atan2(y2 - y1, x2 - x1)
    heading = math.degrees(heading)
    heading = math.fmod(heading - 360, 360)
    return abs(heading)

def calculateDistance(x1, y1, x2, y2):
    headingX = x2 - x1
    headingY = y2 - y1
    return math.sqrt((headingX * headingX) + (headingY * headingY))

def tryMove(myTank, x2, y2, distance=None, alignTurret=False, shift=0):
    heading = getHeading(myTank['X'], myTank['Y'], x2, y2)
    if abs(myTank['Heading'] - heading) > headingErrorMove:
        GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {'Amount': heading + shift})
    elif alignTurret and abs(myTank['TurretHeading'] - heading) > 15:  # only for watching
        GameServer.sendMessage(ServerMessageTypes.TURNTURRETTOHEADING, {'Amount': heading})
    else:
        if not distance:
            distance = calculateDistance(myTank['X'], myTank['Y'], x2, y2)
        GameServer.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE, {'Amount': distance})
        global stationaryTime
        stationaryTime = 0

class Info(object):
    def __init__(self):
        # Objects
        self.myTank = None
        self.enemies = {}
        self.healthPickups = {}
        self.ammoPickups = {}
        self.snitch = None

        # Other Info
        self.snitchPickedUp = None
        self.destroyed = False
        self.enteredGoal = False
        self.didKill = False
        self.snitchAppeared = False
        self.timeLeft = None
        self.hitDetected = False
        self.didHit = False

    def update(self, message):
        if message['messageType'] == ServerMessageTypes.OBJECTUPDATE:
            if message['Type'] == 'Tank':
                if message['Name'] == args.name:
                    self.myTank = message
                else:
                    self.enemies[message['Id']] = {'obj': message, 'time': 0}
            elif message['Type'] == 'HealthPickup':
                self.healthPickups[message['Id']] = {'obj': message, 'time': 0}
            elif message['Type'] == 'AmmoPickup':
                self.ammoPickups[message['Id']] = {'obj': message, 'time': 0}
            elif message['Type'] == 'Snitch':
                self.snitch = {'obj': message, 'time': 0}
            else:
                print('Unrecognized message type:', message)
        elif message['messageType'] == ServerMessageTypes.SNITCHPICKUP:
            self.snitchPickedUp = message['Id']
            self.snitch = None
        elif message['messageType'] == ServerMessageTypes.DESTROYED:
            self.destroyed = True
        elif message['messageType'] == ServerMessageTypes.ENTEREDGOAL:
            self.enteredGoal = True
        elif message['messageType'] == ServerMessageTypes.KILL:
            self.didKill = True
        elif message['messageType'] == ServerMessageTypes.SNITCHAPPEARED:
            self.snitchAppeared = True
        elif message['messageType'] == ServerMessageTypes.GAMETIMEUPDATE:
            self.timeLeft = message['Time']
        elif message['messageType'] == ServerMessageTypes.HITDETECTED:
            self.hitDetected = True
        elif message['messageType'] == ServerMessageTypes.SUCCESSFULLHIT:
            self.didHit = True

    def out(self):
        print('health:', self.myTank['Health'], 'ammo:', self.myTank['Ammo'], 'enemies:', len(self.enemies), 'healthPickups:', len(self.healthPickups), 'ammoPickups:', len(self.ammoPickups))

    def next(self):
        def forget(dic):
            toRemove = []
            for key, value in dic.items():
                value['time'] += waitTime
                if value['time'] > memoryTime:
                    toRemove.append(key)
            for key in toRemove:
                del dic[key]

        forget(self.enemies)
        forget(self.healthPickups)
        forget(self.ammoPickups)

        if self.snitch:
            self.snitch['time'] += waitTime
            if self.snitch['time'] > memoryTime:
                self.snitch = None

        self.snitchPickedUp = None
        self.destroyed = False
        self.enteredGoal = False
        self.didKill = False
        self.snitchAppeared = False
        self.timeLeft = None
        self.hitDetected = False
        self.didHit = False

class States(object):
    SCAN = 'SCAN'
    ATTACK_TARGET = 'ATTACK_TARGET'
    SEARCH_HEALTH = 'SEARCH_HEALTH'
    PICKUP_HEALTH = 'PICKUP_HEALTH'
    SEARCH_AMMO = 'SEARCH_AMMO'
    PICKUP_AMMO = 'PICKUP_AMMO'
    SEARCH_SNITCH = 'SEARCH_SNITCH'
    PICKUP_SNITCH = 'PICKUP_SNITCH'
    BANK_POINTS = 'BANK_POINTS'

def transiteState(currentState, info):
    # Special cases
    if info.snitchPickedUp == info.myTank['Id']:
        return States.BANK_POINTS
    if info.didKill:
        return States.BANK_POINTS
    if info.snitch:
        return States.PICKUP_SNITCH
    # if info.snitchAppeared and currentState != States.BANK_POINTS:
    # 	return States.SEARCH_SNITCH

    if currentState == States.SCAN:
        # if info.snitchAppeared:
        # 	return States.SEARCH_SNITCH
        if info.myTank['Health'] <= healthThresh:
            return States.SEARCH_HEALTH
        if info.snitch:
            return States.PICKUP_SNITCH
        if info.myTank['Ammo'] <= ammoThresh:
            return States.SEARCH_AMMO
        if info.enemies:
            return States.ATTACK_TARGET

    elif currentState == States.SEARCH_HEALTH:
        if info.myTank['Health'] == maxHealth:
            return States.SCAN
        if info.healthPickups:
            return States.PICKUP_HEALTH

    elif currentState == States.SEARCH_AMMO:
        if info.myTank['Ammo'] == maxAmmo:
            return States.SCAN
        if info.myTank['Health'] <= healthThresh:
            return States.SEARCH_HEALTH
        if info.ammoPickups:
            return States.PICKUP_AMMO

    elif currentState == States.SEARCH_SNITCH:
        # if info.myTank['Health'] <= healthThresh:  # which is prior: health or snitch?
        # 	return States.SEARCH_HEALTH
        if info.snitchPickedUp != info.myTank['Id']:
            return States.SCAN

    elif currentState == States.PICKUP_HEALTH:
        if info.myTank['Health'] == maxHealth:
            return States.SCAN
        if not info.healthPickups:
            return States.SEARCH_HEALTH

    elif currentState == States.PICKUP_AMMO:
        if info.myTank['Ammo'] == maxAmmo:
            return States.SCAN
        if not info.ammoPickups:
            return States.SEARCH_AMMO

    elif currentState == States.PICKUP_SNITCH:
        if info.snitchPickedUp != info.myTank['Id']:
            return States.SCAN

    elif currentState == States.ATTACK_TARGET:
        if not info.enemies:
            return States.SCAN
        if info.myTank['Health'] <= healthThresh:
            return States.SEARCH_HEALTH
        if info.myTank['Ammo'] <= ammoThresh:
            return States.SEARCH_AMMO

    elif currentState == States.BANK_POINTS:
        if info.enteredGoal:
            return States.SCAN

    else:
        print('Undefined state.')
        exit()

    return currentState

def getLine(x, y, b):
    m = (b - 90) / 360
    c = y - m * x
    return m, c

def target(a, b, c, d, speed_e, speed_b, m, k):
    # a enemy_x
    # b enemy_y
    # c me_x
    # d me_y

    x = 0.0
    y = 0.0

    a = ( m**2 + 1 ) * ( speed_b - speed_e )
    b = speed_b * ( -2*c + 2*m*g - 2*m*d ) - speed_e * ( -2*a + 2*m*g - 2*m*b )
    c = speed_b * ( a**2 + g**2 - 2*g*b + b**2 ) - speed_b * ( a**2 + g**2 - 2*g*d + d**2 )

    x = quadratic(a, b, c)
    y = m * x + k
    return x, y

def quadratic(a, b, c):
    return -2*b + Math.sqrt(b**2 - 4*a*c)

def performAction(currentState, info):
    if currentState == States.SCAN or currentState == States.SEARCH_HEALTH or currentState == States.SEARCH_AMMO or currentState == States.SEARCH_SNITCH:
        if calculateDistance(info.myTank['X'], info.myTank['Y'], 0, 0) > 15:
            tryMove(info.myTank, ((info.myTank['X']>0)*2-1)*10, ((info.myTank['Y']>0)*2-1)*10, alignTurret=True)  # go to a point closer to center
        else:
            GameServer.sendMessage(ServerMessageTypes.TURNTURRETTOHEADING, {'Amount': math.fmod(info.myTank['TurretHeading']+60, 360)})

    elif currentState == States.PICKUP_HEALTH or currentState == States.PICKUP_AMMO or currentState == States.PICKUP_SNITCH:
        if currentState == States.PICKUP_HEALTH:
            healthPickup = list(info.healthPickups.values())[0]['obj']
            x2 = healthPickup['X']
            y2 = healthPickup['Y']
        elif currentState == States.PICKUP_AMMO:
            ammoPickup = list(info.ammoPickups.values())[0]['obj']
            x2 = ammoPickup['X']
            y2 = ammoPickup['Y']
        elif currentState == States.PICKUP_SNITCH:
            x2 = info.snitch['obj']['X']
            y2 = info.snitch['obj']['Y']
        tryMove(info.myTank, x2, y2, alignTurret=True)

    elif currentState == States.ATTACK_TARGET:
        enemy = list(info.enemies.values())[0]['obj']  # TODO: sort enermies
        x2 = enemy['X']
        y2 = enemy['Y']

        heading = getHeading(info.myTank['X'], info.myTank['Y'], x2, y2)
        distance = calculateDistance(info.myTank['X'], info.myTank['Y'], x2, y2)
        if distance > expectedDist:
            # if abs(info.myTank['TurretHeading'] - heading) < 10:  # try to fire when moving to enemy
            # 	if random.randint(0,10) > 5:
            # 		GameServer.sendMessage(ServerMessageTypes.FIRE)
            # 	else:
            # 		tryMove(info.myTank, x2, y2, distance=distance-expectedDist, alignTurret=True)
            # else:
            # 	tryMove(info.myTank, x2, y2, distance=distance-expectedDist, alignTurret=True)
            tryMove(info.myTank, x2, y2, distance=distance-expectedDist, alignTurret=True)
        else:
            # # rotate body for moving
            # h1 = (heading - 90) % 360
            # h2 = (heading + 90) % 360
            # if (info.myTank['Heading'] - h1) % 360 > 40 \
            # 		and abs(info.myTank['Heading'] - h2) > 40:
            # 	GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {'Amount': fmod(info.myTank['Heading']+45, 360)})
            # else:

            # if stationaryTime > allowedStationaryTime:  # should keep moving to avoid getting hit
            # 	tryMove(info.myTank, info.myTank['X']+random.randint(-5,5), info.myTank['Y']+random.randint(-5,5))
            # else:
            if abs(info.myTank['TurretHeading'] - heading) > headingErrorFire:
                GameServer.sendMessage(ServerMessageTypes.TURNTURRETTOHEADING, {'Amount': heading})
            else:
                GameServer.sendMessage(ServerMessageTypes.FIRE)

    elif currentState == States.BANK_POINTS:
        x2 = y2 = None

        # choose nearest point (coord x) on goal zone
        if info.myTank['X'] > 10:
            x2 = 10
        elif info.myTank['X'] < -10:
            x2 = -10
        else:
            x2 = info.myTank['X']

        # left or right zone
        if info.myTank['Y'] > 0:
            y2 = 105
        else:
            y2 = -105

        tryMove(info.myTank, x2, y2)

    else:
        print('Undefined state.')
        exit()

currentState = States.SCAN
info = Info()

while True:
    info.next()
    while True:
        startTime = time.time()
        message = GameServer.readMessage()
        # try:
        # 	message = GameServer.readMessage()
        # except struct.error:
        # 	print('struct.error')
        # 	continue
        info.update(message)
        if time.time() - startTime > waitTime * 0.001:
            break

    # Add stationaryTime
    stationaryTime += waitTime

    # Respawn tank if died
    if info.destroyed:
        GameServer.sendMessage(ServerMessageTypes.CREATETANK, {'Name': args.name})
        continue

    # Check required info (shouldn't be required now)
    if info.myTank is None or info.myTank['Health'] == 0:
        continue

    # State transition
    info.out()
    print('state before:', currentState)
    currentState = transiteState(currentState, info)
    print('state after', currentState)

    # Perform action
    performAction(currentState, info)

    print()

# i = 0
# ammoPos = []
# healthPos = []
# turretHead = []
# while True:
#     message = GameServer.readMessage()
#     if message['Name']=="":

#         if message['Type']=="AmmoPickup":
#             ammoPos.append((message['X'], message['Y']))
#         if message['Type']=="HealthPickup":
#             healthPos.append(())

#         while True:
#             dist =
#             angle =
#             GameServer.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE, {'Amount': min(10, )})
#     if message['Name']=="RandomBot":
#         turretHead[]
#     logging.info(message)

#     if i<=10:
#         logging.info("Turning randomly")
#         logging.info("Firing")
#         GameServer.sendMessage(ServerMessageTypes.FIRE)
#         GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {'Amount': random.randint(0, 359)})
#     elif i <=15:
#         logging.info("Moving randomly")
#         GameServer.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE, {'Amount': random.randint(0, 10)})
#     if message['Name'] == "RandonBot" and message['Type']=="Tank":
#         if message['Ammo']<=5:
#             GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {'Amount': random.randint(0, 359)})

#     i = i + 1
#     if i > 20:
#         i = 0
