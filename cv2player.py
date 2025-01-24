import random

def attack():
    damage = random.randint(20,30)
    critical = random.randint(1,100)
    if critical<=5:
        return damage*2
    else:
        return damage

def defence(damaged):
    damaged = int(damaged/2)
    return damaged

def special(mp):
    if mp < 30:
        return mp,0
    else:
        mp = mp-30
        damage = 25
        bougyo = True
        return mp,damage,bougyo
    
def kaihuku(hp,kaisuu):
    if kaisuu > 3:
        return hp
    else:
        hp = hp + 30
        return hp
    