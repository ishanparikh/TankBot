#!/bin/python

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
