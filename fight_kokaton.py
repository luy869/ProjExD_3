import os
import random
import sys
import time
import pygame as pg
import math

NUM_OF_BOMBS = 5 #爆弾の数
WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
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
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/9.png"), 0, 0.9)
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
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
        screen.blit(self.img, self.rct)

class Score:
    """
    消した爆弾の数を表示するクラス
    """
    def __init__(self):
        self.fonto = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (0, 0, 255)  # 青色
        self.score = 0  # スコアの初期値
        self.img = self.fonto.render(f"スコア：{self.score}", 0, self.color)
        self.rct = self.img.get_rect()
        self.rct.topleft = (100, HEIGHT-50)  # 画面左下（横座標100、縦座標は画面下部から50）
    
    def update(self, screen):
        """
        現在のスコアを表示させる文字列Surfaceの生成
        スクリーンにblit
        """
        self.img = self.fonto.render(f"スコア：{self.score}", 0, self.color)
        screen.blit(self.img, self.rct)
    
    def add_score(self, pts=1):
        """
        スコアを加算する
        引数 pts：加算する点数（デフォルト1点）
        """
        self.score += pts
        
class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん（Birdインスタンス）
        """
        self.img = pg.image.load("fig/beam.png")
        self.rct = pg.Rect(bird.rct.centerx, bird.rct.centery, 10, 10)
        self.vx, self.vy = +5, 0

    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        if check_bound(self.rct) == (True, True):
            self.rct.move_ip(self.vx, self.vy)
            screen.blit(self.img, self.rct)  

    

class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, vxy, velocity):
        """
        爆弾を初期化する
        引数1 vxy：爆弾の初期座標のタプル
        引数2 velocity：爆弾の速度のタプル（例：(5, 5)）
        """
        rad = 10  # ここで半径を明示的に設定
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, (255, 0, 0), (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = vxy
        self.vx, self.vy = velocity  # velocity タプルから速度成分を取得

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


def gameover(screen):
    font = pg.font.Font(None, 80)
    txt = font.render("Game Over", True, (255, 0, 0))
    screen.blit(txt, [WIDTH/2 - 150, HEIGHT/2])
    pg.display.update()
    time.sleep(3)


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    beam = None
    score = Score()
    clock = pg.time.Clock()
    
    # tmrを初期化
    tmr = 0
    
    # 複数の爆弾を格納するリスト
    bombs = []
    for i in range(NUM_OF_BOMBS):
        vx, vy = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        bomb = Bomb((vx, vy), (1, 1))  
        bombs.append(bomb)

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下でBeamクラスのインスタンス生成
                beam = Beam(bird)            
        screen.blit(bg_img, [0, 0])
        
        # 爆弾とビームの衝突判定
        if bomb is not None and beam is not None:
            if beam.rct.colliderect(bomb.rct):
                # 衝突したら両方をNoneにして消滅させる
                beam = None
                bomb = None
                bird.change_img(9, screen)
                


        # こうかとんと爆弾の衝突判定
        if bomb is not None:
            if bird.rct.colliderect(bomb.rct):
                # 衝突したらゲームオーバー
                gameover(screen)

        key_lst = pg.key.get_pressed()
        if bomb is not None:
            bomb.update(screen)

        if beam is not None:
            beam.update(screen)
    
        # 爆弾とこうかとんの衝突判定
        for bomb in bombs:
            if bomb is not None:
                if bird.rct.colliderect(bomb.rct):
                    gameover(screen)
                    return
    
        # 爆弾とビームの衝突判定（
        if beam is not None:
            for i, bomb in enumerate(bombs):
                if bomb is not None and beam.rct.colliderect(bomb.rct):
                    bombs[i] = None  # 爆弾をNoneに設定
                    beam = None
                    score.add_score()
                    bird.change_img(tmr, screen)
                    break

    
        # 爆弾リストをNoneでない要素だけに更新
        bombs = [bomb for bomb in bombs if bomb is not None]
        
        # 残った爆弾の更新
        for bomb in bombs:
            bomb.update(screen)
    
        bird.update(key_lst, screen)

        if bomb is not None:
            screen.blit(bomb.img, bomb.rct)
        if beam is not None:
            screen.blit(beam.img, beam.rct)
        screen.blit(bird.img, bird.rct)

        # スコアの更新
        score.update(screen)

        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
