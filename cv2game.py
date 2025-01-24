import cv2
import numpy as np 
import cv2.data
import random
import time
from cv2player import*
import math
from PIL import ImageFont, ImageDraw, Image

    



capture = cv2.VideoCapture(0)

#ステータス
player_maxhp = player_hp = 100
player_mp = 100
enemy_maxhp = enemy_hp = 150 

#回復回数とダメージ
kaisuu = 0
damage = 10

#時間設定
choice_limit = 7
enemy_end = 19

#各イベントのフラグ
bougyo = False
action_flag = False
dogde_flag = False

#カメラのサイズ変更
def camera_with_custom_size(width, height):
    global capture
    
    # カメラが正常にオープンされたか確認
    if not capture.isOpened():
        print("カメラを開けませんでした")
        return
    
    # カメラのプロパティを設定
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)


camera_with_custom_size(640,640)

w = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
print(w,h)

devil = cv2.imread('fantasy_maou_devil.png',-1)

def scale_to_width(img, width):
    """幅が指定した値になるように、アスペクト比を固定して、リサイズする。
    """
    h, w = img.shape[:2]
    height = round(h * (width / w))
    dst = cv2.resize(img, dsize=(width, height))

    return dst

# フルーツ画像リサイズ
devil_size = 150

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
ball_x = 300
ball_y = 250
ball_size = 10
balls = []

for i in range(10):
    a = random.randint(-20,-10)
    b = random.randint(10,20)
    if abs(a)>=abs(b):
        speed_x = a
    else:
        speed_x = b
    speed_y = random.randint(10,20)
    ball_angle = random.randint(-30,30)
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

          
last_event_time = time.time()

while(True):
    ret, frame = capture.read()
    frame = cv2.flip(frame, 1)
    frame = CvOverlayImage.overlay(frame, devil,(240,200))
    gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
   
   #ステータス表示
    cv2.putText(frame, f'Player HP: {player_hp}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (30, 255, 0), 2)
    cv2.putText(frame, f'Player MP: {player_mp}', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
    cv2.putText(frame, f'Cure rest: {3-kaisuu}', (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    cv2.putText(frame, f'Enemy HP: {enemy_hp}', (350, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    #ステータスバー表示
    cv2.line(frame,(150,30),(int(150+100*player_hp/player_maxhp),30),(0, 255, 0), 3)
    cv2.line(frame,(150,60),(int(150+100*player_mp/100),60),(255, 255, 0), 3)
    cv2.line(frame,(490,30),(int(490+100*enemy_hp/enemy_maxhp),30),(0, 0, 255), 3)
    
    # 顔を検出
    face = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30,30))
    if 2 > len(face) > 0:
        for rect in face:
            if not right_side(rect) and up_side(rect):
                line = cv2.line(frame, (rect[0],rect[1]), (rect[0]+rect[3],rect[1]),(0,0,255), thickness =2)
            elif right_side(rect) and up_side(rect):
               line = cv2.line(frame, (rect[0],rect[1]), (rect[0]+rect[3],rect[1]),(255,0,0), thickness =2)
            elif not right_side(rect) and not up_side(rect):
                line = cv2.line(frame, (rect[0],rect[1]), (rect[0]+rect[3],rect[1]),(0,255,0), thickness =2)
            else:
                line = cv2.line(frame, (rect[0],rect[1]), (rect[0]+rect[3],rect[1]),(0, 255, 255), thickness =2)
    
    choice_time = time.time()
    
    #コマンドや制限時間の表示
    if action_flag == False:
        cv2.putText(frame, "Attack", (100, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(frame, "Guard", (400, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        cv2.putText(frame, "Cure", (100, 400), cv2.FONT_HERSHEY_SIMPLEX, 1, (30, 255, 0), 2)
        cv2.putText(frame, "Special", (400, 400), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.putText(frame, f"{int(choice_limit-(choice_time - last_event_time))}",(300,150),cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
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
    if 9<= choice_time - last_event_time <=enemy_end and dogde_flag == False:
        cv2.putText(frame, "enemy attack", (100, 100),cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255),3)
        cv2.putText(frame, f"{int(enemy_end-(choice_time - last_event_time))}",(300,150),cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

        for ball in balls:
            cv2.circle(frame,(ball[0],ball[1]),ball_size,(255,0,0),-1)
            move_ball(ball[2],ball[3])
            
            for rect in face:
                if rect[0]<= ball[0]<=rect[0]+rect[3] and ball[1]==rect[1] and bougyo == True:
                    player_hp -= defence(damage)
                if rect[0]<= ball[0]<=rect[0]+rect[3] and ball[1]==rect[1] and bougyo == False:
                    player_hp -= damage
                    
    if choice_time - last_event_time >=17 and player_hp > 0 and enemy_hp > 0:
        action_flag = False
        bougyo = False
        last_event_time = choice_time
        for ball in balls:
            ball[0] = 300
            ball[1] = 250
    
    if player_hp <= 0:
        action_flag = True
        dogde_flag = True
        cv2.putText(frame, "LOSE", (250, 320), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 2)
    
    if enemy_hp <= 0:
        action_flag = True
        dogde_flag = True
        cv2.putText(frame, "WIN!", (250, 320), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)


        
    cv2.imshow("camera",frame)
    if  cv2.waitKey(1) == ord("q"):
        break
    
capture.release()
cv2.destroyAllWindows()