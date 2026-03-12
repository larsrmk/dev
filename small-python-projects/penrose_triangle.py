import turtle
from turtle import *

width(4)
bgcolor("black")
color("white")

def penrose_triangle():
    up()
    right(90)
    forward(160)
    right(90)
    forward(240)
    right(180)

    for i in range(3):
        if i == 0:
            color("blue")
            fillcolor("blue")
        if i == 1:
            color("pink")
            fillcolor("pink")
        if i == 2:
            color("gold")
            fillcolor("gold")

        begin_fill()
        down()
        forward(480)
        left(60)
        forward(80)
        left(60)
        left(60)
        forward(400)
        right(120)
        forward(240)
        left(60)
        forward(80)
        left(120)
        forward(400)
        end_fill()
#Weg zurücklaufen
        up()
        backward(400)
        right(120)
        backward(80)
        right(60)
        backward(240)
        left(120)
        backward(400)
        right(60)

# schwarzer Rand
    for i in range(3):
        color("black")
        pensize(8)

        down()
        forward(480)
        left(60)
        forward(80)
        left(120)
        forward(400)
        right(120)
        forward(240)
        left(60)
        forward(80)
        left(120)
        forward(400)
# Weg zurücklaufen
        backward(400)
        right(120)
        backward(80)
        right(60)
        backward(240)
        left(120)
        backward(400)
        right(60)

    up()
    forward(240)
    left(90)
    forward(200)


    turtle.exitonclick()

penrose_triangle()