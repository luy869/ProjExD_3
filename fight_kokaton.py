import math
import os
import random
import sys
import time
import pygame as pg

NUM_OF_BOMBS = 5  # 爆弾の数
WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定する関数
    引数 obj_rct：オブジェクト（こうかとんor爆弾）のRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate

class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5), pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0), pg.K_RIGHT: (+5, 0),
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとんの位置座標タプル
        """
        img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
        self.imgs = {
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
        }
        self.img = self.imgs[(+5, 0)]  # デフォルト右向き
        self.rct = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0)  # デフォルト右向き

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.image.load(f"fig/9.png")
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        
        # updateメソッド：合計移動量sum_mvが[0,0]でない時，self.direをsum_mvの値で更新
        if sum_mv != [0, 0]:
            self.dire = tuple(sum_mv)
            self.img = self.imgs[self.dire]
        
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        screen.blit(self.img, self.rct)

class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        self.img = pg.image.load("fig/beam.png")
        
        # Birdのdireにアクセスし、こうかとんが向いている方向をvx, vyに代入
        vx, vy = bird.dire
        
        angle = math.degrees(math.atan2(-vy, vx))
        self.img = pg.transform.rotozoom(self.img, angle, 1.0)
        
        # こうかとんのrctのwidthとheightおよび向いている方向を考慮した初期配置
        self.rct = self.img.get_rect()
        self.rct.centerx = bird.rct.centerx + bird.rct.width * vx // 5
        self.rct.centery = bird.rct.centery + bird.rct.height * vy // 5
        
        self.vx, self.vy = vx, vy

    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)

class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, vxy, velocity):
        rad = 10
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, (255, 0, 0), (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = vxy
        self.vx, self.vy = velocity

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)

class Explosion:
    """
    爆発エフェクトを表示するクラス
    """
    def __init__(self, pos):
        self.imgs = []
        explosion_img = pg.image.load("fig/explosion.gif")
        self.imgs.append(explosion_img)
        self.imgs.append(pg.transform.flip(explosion_img, True, False))
        self.imgs.append(pg.transform.flip(explosion_img, False, True))
        self.imgs.append(pg.transform.flip(explosion_img, True, True))
        
        self.rct = explosion_img.get_rect()
        self.rct.center = pos
        self.life = 100

    def update(self, screen):
        self.life -= 1
        if self.life > 0:
            img_index = (100 - self.life) // 5 % len(self.imgs)
            screen.blit(self.imgs[img_index], self.rct)
            return True
        else:
            return False

class Score:
    """
    消した爆弾の数を表示するクラス
    """
    def __init__(self):
        self.fonto = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (0, 0, 255)
        self.score = 0
        self.img = self.fonto.render("スコア：0", 0, self.color)
        self.rct = self.img.get_rect()
        self.rct.topleft = (100, HEIGHT-50)
    
    def update(self, screen):
        self.img = self.fonto.render(f"スコア：{self.score}", 0, self.color)
        screen.blit(self.img, self.rct)
    
    def add_score(self, pts=1):
        self.score += pts

def gameover(screen):
    """
    ゲームオーバー画面を表示し、5秒後に終了する
    """
    font = pg.font.Font(None, 80)
    txt = font.render("Game Over", True, (255, 0, 0))
    screen.blit(txt, [WIDTH/2 - 150, HEIGHT/2])
    pg.display.update()
    time.sleep(5)

def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    beams = []
    clock = pg.time.Clock()
    frame_count = 0
    score = Score()
    explosions = []
    
    # 爆弾の生成
    bombs = []
    for i in range(NUM_OF_BOMBS):
        vx, vy = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        bomb = Bomb((vx, vy), (1, 1))  
        bombs.append(bomb)

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            elif event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.append(Beam(bird))
        
        key_lst = pg.key.get_pressed()
        screen.blit(bg_img, [0, 0])
        
        # こうかとんと爆弾の衝突判定
        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
                gameover(screen)
                return
    
        # ビームと爆弾の衝突判定
        for i, beam in enumerate(beams):
            if beam is not None:
                for j in range(len(bombs)-1, -1, -1):
                    if bombs[j] is not None and beam.rct.colliderect(bombs[j].rct):
                        explosion = Explosion(bombs[j].rct.center)
                        explosions.append(explosion)
                        
                        del bombs[j]
                        beams[i] = None
                        score.add_score(1)
                        bird.change_img(frame_count, screen)
                        break

        # リストの更新
        beams = [beam for beam in beams if beam is not None and check_bound(beam.rct)[0]]
        
        # 爆弾とビームの更新
        for bomb in bombs:
            bomb.update(screen)
        
        for beam in beams:
            beam.update(screen)
    
        # 爆発エフェクトの更新
        active_explosions = []
        for explosion in explosions:
            if explosion.update(screen):
                active_explosions.append(explosion)
        explosions = active_explosions
        
        bird.update(key_lst, screen)
        score.update(screen)

        pg.display.update()
        frame_count += 1
        clock.tick(50)

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
