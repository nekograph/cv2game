import random

class Player():
    
    def __init__(self,hp,mp,remind,power):
        
        self.max_hp = self.hp = hp
        self.mp = mp
        self.Cure_remind = remind
        self.power = power
        
    
    #攻撃　ランダムでダメージを与えて35％の確率でクリティカル
    def attack(self,target):
        damage = random.randint(self.power,self.power+10)
        critical = random.randint(1,100)
        
        if critical<=35:
            target.hp -= damage*2
        else:
            target.hp -= damage
    
    #防御　次に受けるダメージを半分にする
    def defence(self,receive_damage):
        receive_damage /= 2
        return receive_damage
        
    #スペシャル技　mpを30使って相手に25ダメージ．
    # さらに次に受けるダメージを半分にする
    def special(self,target):
        magic_need = 30
        if self.mp < magic_need:
            return
        else:
            self.mp -= magic_need
            damage = self.power + 5
            target.hp -= damage
            bougyo = True
            return bougyo
    
    #回復　hpを30増やす．
    def kaihuku(self):
        
        if self.Cure_remind <= 0:
            return 
        else:
            self.hp += 30
            self.Cure_remind -= 1

class Enemy():
    
    def __init__(self,hp,power):
        self.max_hp = self.hp = hp
        self.power = power
    
    
    
        
    
    
        
    
    
