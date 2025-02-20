import cv2
import pygame
import numpy as np
import random
import time
from cv2player import*
import math
import sys
from PIL import ImageFont, ImageDraw, Image




#ステータス
player_maxhp = player_hp = 100
player_mp = 100
enemy_maxhp = enemy_hp = 150 

#回復回数とダメージ
kaisuu = 0
damage = 5

#時間設定
choice_limit = 7
enemy_turn_time = 20

#各イベントのフラグ
bougyo = False
action_flag = False
finish_flag = False



devil = cv2.imread('fantasy_maou_devil.png',-1)

def scale_to_width(img, width):
    """幅が指定した値になるように、アスペクト比を固定して、リサイズする。
    """
    h, w = img.shape[:2]
    height = round(h * (width / w))
    dst = cv2.resize(img, dsize=(width, height))

    return dst

# 画像リサイズ
devil_size = 200

devil = scale_to_width(devil,devil_size)

class CvOverlayImage(object):
    """
    [summary]
      OpenCV形式の画像に指定画像を重ねる
    """

    def __init__(self):
        pass

    @classmethod
    def overlay(
            cls,
            cv_background_image,
            cv_overlay_image,
            point,
    ):
        """
        [summary]
          OpenCV形式の画像に指定画像を重ねる
        Parameters
        ----------
        cv_background_image : [OpenCV Image]
        cv_overlay_image : [OpenCV Image]
        point : [(x, y)]
        Returns : [OpenCV Image]
        """
        overlay_height, overlay_width = cv_overlay_image.shape[:2]

        # OpenCV形式の画像をPIL形式に変換(α値含む)
        # 背景画像
        cv_rgb_bg_image = cv2.cvtColor(cv_background_image, cv2.COLOR_BGR2RGB)
        pil_rgb_bg_image = Image.fromarray(cv_rgb_bg_image)
        pil_rgba_bg_image = pil_rgb_bg_image.convert('RGBA')
        # オーバーレイ画像
        cv_rgb_ol_image = cv2.cvtColor(cv_overlay_image, cv2.COLOR_BGRA2RGBA)
        pil_rgb_ol_image = Image.fromarray(cv_rgb_ol_image)
        pil_rgba_ol_image = pil_rgb_ol_image.convert('RGBA')

        # composite()は同サイズ画像同士が必須のため、合成用画像を用意
        pil_rgba_bg_temp = Image.new('RGBA', pil_rgba_bg_image.size,
                                     (255, 255, 255, 0))
        # 座標を指定し重ね合わせる
        pil_rgba_bg_temp.paste(pil_rgba_ol_image, point, pil_rgba_ol_image)
        result_image = \
            Image.alpha_composite(pil_rgba_bg_image, pil_rgba_bg_temp)

        # OpenCV形式画像へ変換
        cv_bgr_result_image = cv2.cvtColor(
            np.asarray(result_image), cv2.COLOR_RGBA2BGRA)

        return cv_bgr_result_image

#ボール（敵の攻撃）について
ball_x = None
ball_y = 250
ball_size = 10
balls = []

for i in range(20):
    a = random.randint(-20,-10)
    b = random.randint(10,20)
    if abs(a)>=abs(b):
        speed_x = a
    else:
        speed_x = b
    speed_y = random.randint(10,20)
    ball_angle = random.randint(-90,90)
    #xの位置,yの位置,x方向のスピード,y方向のスピード,角度
    balls.append([ball_x,ball_y,speed_x,speed_y,ball_angle])

#壁が下にある時の反射
def ball_reflection_down(y):
    global balls
    if ball[1] >= y:
        ball[4] = -ball[4]
        ball[1] = y
    
#壁が上にある時の反射
def ball_reflection_up(y):
    global balls
    if ball[1] <= y:
        ball[4] = -ball[4]
        ball[1] = y
    
#壁が左にある時の反射
def ball_reflection_left(x):
    global balls
    if ball[0] >= x:
        ball[4] = 180-ball[4]
        ball[0] = x
   
#壁が右にある時の反射     
def ball_reflection_right(x):
    global balls
    if ball[0] <= x:
        ball[4] = 180-ball[4]
        ball[0] = x
    

def move_ball(ball_x_speed,ball_y_speed):
    global balls,w,h
    # ボール移動
    ball[0] += round(math.cos(math.radians(ball[4]))*ball_x_speed)
    ball[1] += round(math.sin(math.radians(ball[4]))*ball_y_speed)

    ball_reflection_right(0)
    ball_reflection_left(w)
    ball_reflection_up(0)
    ball_reflection_down(h)

      
    if ball[4] > 360:
        ball[4] -= 360

#カメラの上下左右を判断
def right_side(rect):
    global w
    if rect[0]+rect[3]/2>=w/2:
        return True
    
def up_side(rect):
    global h
    if rect[1]<=h/2:
        return True


        

#ゲームの初期化
pygame.init()

#タイトル画面
screen = pygame.display.set_mode((0,0),pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()

pygame.display.set_caption("タイトル画面")

#フォント
font = pygame.font.Font(None,50)
font_title= pygame.font.Font(None,100)
font_asobi = pygame.font.Font("C:/Windows/Fonts/msgothic.ttc",30)

#テキスト
current = "title"
text_title = font_title.render("Camera RPG Battle",True,(0,0,0))
text_title_w,text_title_h = text_title.get_size()
text_how_to_play =  ["顔を使ったRPG風バトルゲーム",
                     "顔を動かしてコマンドを選択,顔に出ている線の色によって行動が決まる",
                     "Attackは敵に攻撃",
                     "Guardは次の敵から受けるダメージを半減",
                     "Cureは自分の体力を30回復，3回まで使える",
                     "SpecialはMPを30使って攻撃しつつ次の敵のダメージを半減",
                     "自分のターンが終わると敵のターン",
                     "敵が青い球をいくつか出す",
                     "それが顔の線に当たるとダメージを食らう",
                     "敵のhpを0にすると勝ち，自分のhpが0になると負け"]

# メインループ
running = True
how_to_play = False
camera_started = False



class Button:
    def __init__(self, x, y, width, height, text, color, text_color, action):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.text = font.render(text,True,text_color)
        
        # 文字のサイズを取得して中央に配置
        text_width, text_height = self.text.get_size()
        self.text_x = x + (width - text_width) // 2
        self.text_y = y + (height - text_height) // 2
        self.action = action

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        screen.blit(self.text, (self.text_x, self.text_y))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


def start_game():
    global running, camera_started
    running = False
    camera_started = True
    
def how_to():
    global current
    current ="how_to_play_game"

def back_to_title():
    global current
    current ="title"
    
button_1 = Button(WIDTH//5,2*HEIGHT/3-100,200,100,"play game",(0,255,0),(255,255,255),start_game)
button_2 = Button(WIDTH-WIDTH//3,2*HEIGHT/3-100,200,100,"how to play",(0,255,255),(255,255,255),how_to)
button_3 = Button(WIDTH-WIDTH//3,HEIGHT-300,200,100,"Exit",(0,255,255),(255,255,255),back_to_title)

while running:
    screen.fill((200,200,0))
    if current == "title":
        screen.blit(text_title,((WIDTH-text_title_w)//2,HEIGHT/3))
        button_1.draw(screen)
        button_2.draw(screen)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if pygame.K_DELETE:
                    running = False
                    sys.exit()
                    
            elif event.type == pygame.MOUSEBUTTONUP:    
                if button_2.is_clicked(event.pos):
                    button_2.action()
                    break
                
                elif button_1.is_clicked(event.pos):
                    button_1.action()
                    break
    
    elif current == "how_to_play_game":
        y_offset = 100
        button_3.draw(screen)
        
        for rule in text_how_to_play:
            if rule == "Attackは敵に攻撃":
                text_rule = font_asobi.render(rule,True,(255,0,0))
            elif rule == "Guardは次の敵から受けるダメージを半減":
                text_rule = font_asobi.render(rule,True,(0,0,255))
            elif rule == "Cureは自分の体力を30回復，3回まで使える":
                text_rule = font_asobi.render(rule,True,(0,128,0))
            elif rule == "SpecialはMPを30使って攻撃しつつ次の敵のダメージを半減":
                text_rule = font_asobi.render(rule,True,(255,255,0))
            else:
                text_rule = font_asobi.render(rule,True,(0,0,0))

            screen.blit(text_rule,(50,y_offset))
            y_offset+=40
        
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if pygame.K_DELETE:
                    running = False
                    sys.exit()
                    
            if event.type == pygame.MOUSEBUTTONUP:
                if button_3.is_clicked(event.pos):
                    button_3.action()
               
           
        
                
    pygame.display.flip()  # 画面更新

pygame.quit()  # Pygame終了


if camera_started == True:   
    last_event_time = None
                
    capture = cv2.VideoCapture(0)
    cv2.namedWindow('camera',cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('camera',cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
    
    
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
    w,h = cv2.getWindowImageRect("camera")[2:4]
    
    for ball in balls:
        ball[0] = int(w/2)
    
    while(True):
        
        ret, frame = capture.read()
        frame = cv2.flip(frame, 1)
        frame_resize = cv2.resize(frame,(w,h))
        
        #カメラを表示してからタイマーを計測
        if not ret:
            continue
        if last_event_time == None:
            last_event_time = time.time()
        
        #悪魔の画像をカメラに出す．
        if enemy_hp > 0 and player_hp >0:
            frame_resize = CvOverlayImage.overlay(frame_resize, devil,(int(w/2)-100,250))
        gray = cv2.cvtColor(frame_resize,cv2.COLOR_BGR2GRAY)
    
    #ステータス表示
        cv2.putText(frame_resize, f'Player HP: {player_hp}', (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (30, 255, 0), 2)
        cv2.putText(frame_resize, f'Player MP: {player_mp}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        cv2.putText(frame_resize, f'Cure rest: {3-kaisuu}', (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,128,0), 2)
        cv2.putText(frame_resize, f'Enemy HP: {enemy_hp}', (w-500, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        #ステータスバー表示
        cv2.line(frame_resize,(300,30),(int(300+150*player_hp/player_maxhp),30),(0, 255, 0), 3)
        cv2.line(frame_resize,(300,60),(int(300+150*player_mp/100),60),(255, 255, 0), 3)
        cv2.line(frame_resize,(w-200,30),(int(w-200+150*enemy_hp/enemy_maxhp),30),(0, 0, 255), 3)
        
        # 顔を検出
        face = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30,30))
        if 2 > len(face) > 0:
            for rect in face:
                if not right_side(rect) and up_side(rect):
                    line = cv2.line(frame_resize, (rect[0],rect[1]), (rect[0]+rect[3],rect[1]),(0,0,255), thickness =2)
                elif right_side(rect) and up_side(rect):
                    line = cv2.line(frame_resize, (rect[0],rect[1]), (rect[0]+rect[3],rect[1]),(255,0,0), thickness =2)
                elif not right_side(rect) and not up_side(rect):
                    line = cv2.line(frame_resize, (rect[0],rect[1]), (rect[0]+rect[3],rect[1]),(0,255,0), thickness =2)
                else:
                    line = cv2.line(frame_resize, (rect[0],rect[1]), (rect[0]+rect[3],rect[1]),(0, 255, 255), thickness =2)
        
        choice_time = time.time()
        
        #コマンドや制限時間の表示
        if action_flag == False:
            cv2.putText(frame_resize, "player choice", (int(w/2)-200, 100),cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255),3)
            cv2.putText(frame_resize, "Attack", (int(w/2)-500, int(h/2)-300), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 4)
            cv2.putText(frame_resize, "Guard", (int(w/2)+200, int(h/2)-300), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 0, 0), 4)
            cv2.putText(frame_resize, "Cure", (int(w/2)-500, int(h/2)+300), cv2.FONT_HERSHEY_SIMPLEX, 3, (30, 255, 0), 4)
            cv2.putText(frame_resize, "Special", (int(w/2)+200, int(h/2)+300), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 255), 4)
            cv2.putText(frame_resize, f"{int(choice_limit-(choice_time - last_event_time))}",(int(w/2)-20,180),cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
        
        #プレイヤーのコマンド選択
        if choice_time - last_event_time >= choice_limit and action_flag == False:
            for rect in face:
                if  not right_side(rect) and up_side(rect):
                    enemy_hp -= attack()
                elif not right_side(rect) and not up_side(rect):
                    player_hp = kaihuku(player_hp,kaisuu)
                    kaisuu +=1
                elif right_side(rect) and not up_side(rect):
                    player_mp,bougyo = special(player_mp)[0],special(player_mp)[2]
                    enemy_hp -= special(player_mp)[1]
                else:
                    bougyo = True
            action_flag = True
        
        #敵の攻撃
        if choice_limit +2<= choice_time - last_event_time <=enemy_turn_time and finish_flag == False:
            cv2.putText(frame_resize, "enemy attack", (int(w/2)-200, 100),cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255),3)
            cv2.putText(frame_resize, f"{int(enemy_turn_time-(choice_time - last_event_time))}",(int(w/2)-20,180),cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)

            for ball in balls:
                cv2.circle(frame_resize,(ball[0],ball[1]),ball_size,(255,0,0),-1)
                move_ball(ball[2],ball[3])
                
                # 線にぶつかるとダメージ
                for rect in face:
                    if rect[0]<= ball[0]<=rect[0]+rect[3] and rect[1]-5<=ball[1]<=rect[1]+5 and bougyo == True:
                        player_hp -= defence(damage)
                    if rect[0]<= ball[0]<=rect[0]+rect[3] and rect[1]-5<=ball[1]<=rect[1]+5  and bougyo == False:
                        player_hp -= damage
                    cv2.rectangle(frame_resize,(rect[0],rect[1]-5),(rect[0]+rect[3],rect[1]+5),(0,0,0))
        
        # フラグや防御状態，タイム，ボールの位置をリセット                
        if choice_time - last_event_time >= enemy_turn_time and player_hp > 0 and enemy_hp > 0:
            action_flag = False
            bougyo = False
            last_event_time = choice_time
            for ball in balls:
                ball[0] = int(w/2)
                ball[1] = 250
        
        # 勝ち負けを表示
        if player_hp <= 0:
            action_flag = True
            finish_flag = True
            cv2.putText(frame_resize, "LOSE", (int(w/2)-200, 360), cv2.FONT_HERSHEY_SIMPLEX, 4, (255, 0, 0), 4)
        
        if enemy_hp <= 0:
            action_flag = True
            finish_flag = True
            cv2.putText(frame_resize, "WIN!", (int(w/2)-200, 360), cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 0, 255), 4)


            
        cv2.imshow("camera",frame_resize)
        if  cv2.waitKey(1) == ord("q"):
            break
        
    capture.release()
    cv2.destroyAllWindows()