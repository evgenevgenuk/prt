import sys, subprocess, threading, time, tkinter as tk
from tkinter import ttk, messagebox
import ctypes

for pkg in ["pywin32","keyboard"]:
    try:
        __import__("win32gui" if pkg=="pywin32" else pkg)
    except:
        subprocess.call([sys.executable,"-m","pip","install",pkg,"-q"])

import win32gui, win32con, win32api, keyboard

target_hwnd = None
wins_map = {}
VK_CONSOLE = 0xC0

# ── Укр → Eng розкладка ──────────────────────────────────────
UA_TO_EN = {
    'й':'q','ц':'w','у':'e','к':'r','е':'t','н':'y','г':'u','ш':'i','щ':'o','з':'p',
    'х':'[','ї':']','ф':'a','і':'s','в':'d','а':'f','п':'g','р':'h','о':'j','л':'k',
    'д':'l','ж':';','є':"'",'я':'z','ч':'x','с':'c','м':'v','и':'b','т':'n','ь':'m',
    'б':',','ю':'.','Й':'Q','Ц':'W','У':'E','К':'R','Є':'T','Н':'Y','Г':'U','Ш':'I',
    'Щ':'O','З':'P','Х':'{','Ї':'}','Ф':'A','І':'S','В':'D','А':'F','П':'G','Р':'H',
    'О':'J','Л':'K','Д':'L','Ж':':','Ч':'X','С':'C','М':'V','И':'B','Т':'N','Ь':'M',
}
def ua_to_en(s):
    return ''.join(UA_TO_EN.get(c, c) for c in s)

# ── Натиснути клавішу по VK коду ────────────────────────────
def press_vk(vk):
    scan = win32api.MapVirtualKey(vk, 0)
    win32api.keybd_event(vk, scan, 0, 0)
    time.sleep(0.05)
    win32api.keybd_event(vk, scan, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.05)

def release_mouse():
    ctypes.windll.user32.ClipCursor(None)
    for _ in range(10):
        if ctypes.windll.user32.ShowCursor(True) >= 0: break

def type_and_run(cmd):
    press_vk(VK_CONSOLE); time.sleep(0.3)
    win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
    press_vk(0x41)
    win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.05)
    keyboard.write(cmd, delay=0.04)
    time.sleep(0.1)
    press_vk(win32con.VK_RETURN)
    time.sleep(0.3)
    press_vk(VK_CONSOLE)
    time.sleep(0.2)

def send_cmd(cmd, skip_cheats=False):
    global target_hwnd
    if not target_hwnd: print("[ERR] Вікно не вибрано"); return
    root.withdraw(); time.sleep(0.15)
    try:
        win32gui.ShowWindow(target_hwnd, 9)
        win32gui.SetForegroundWindow(target_hwnd)
    except: pass
    time.sleep(0.4)
    type_and_run(cmd)
    root.deiconify(); root.attributes("-topmost", True)
    root.focus_force(); release_mouse()
    print(f"[OK] {cmd}")

def run_cmd(cmd, skip_cheats=False):
    threading.Thread(target=send_cmd, args=(cmd, skip_cheats), daemon=True).start()

def run_two_cmds(cmd1, cmd2):
    """Відправити дві команди послідовно"""
    def f():
        send_cmd(cmd1)
        time.sleep(0.5)
        send_cmd(cmd2)
    threading.Thread(target=f, daemon=True).start()

# ── Стан ─────────────────────────────────────────────────────
state = {
    "sv_cheats":False,"noclip":False,"god":False,"buddha":False,
    "notarget":False,"thirdperson":False,"fly":False,"fast":False,"slow":False,
}

def ask_enable_cheats():
    """Попередження перед увімкненням sv_cheats"""
    return messagebox.askyesno(
        "sv_cheats",
        "sv_cheats вимкнено!\n\nВключити sv_cheats 1?\n(Увага: скидає деякі прогреси в challenge mode)",
        parent=root
    )

def toggle_cheats():
    if not state["sv_cheats"]:
        if not ask_enable_cheats(): return
    state["sv_cheats"] = not state["sv_cheats"]
    run_cmd("sv_cheats 1" if state["sv_cheats"] else "sv_cheats 0", skip_cheats=True)
    refresh()

def ensure_cheats_gui():
    """Перевірити sv_cheats, запитати якщо вимкнено. Повертає True якщо можна продовжувати."""
    if not state["sv_cheats"]:
        if not ask_enable_cheats(): return False
        state["sv_cheats"] = True
    return True

def mk(key, on_cmd, off_cmd=None):
    def f():
        if not ensure_cheats_gui(): return
        def inner():
            state[key] = not state[key]
            send_cmd(on_cmd if state[key] else (off_cmd or on_cmd))
            refresh()
        threading.Thread(target=inner, daemon=True).start()
    return f

t_noclip      = mk("noclip",     "noclip",          "noclip")
t_god         = mk("god",        "god",             "god")
t_buddha      = mk("buddha",     "buddha",          "buddha")
t_notarget    = mk("notarget",   "notarget",        "notarget")
t_thirdperson = mk("thirdperson","thirdperson",     "firstperson")
t_fly         = mk("fly",        "sv_gravity 100",  "sv_gravity 600")

def t_fast():
    if not ensure_cheats_gui(): return
    def f():
        state["fast"]=not state["fast"]
        if state["fast"]: state["slow"]=False
        send_cmd("host_timescale 3" if state["fast"] else "host_timescale 1"); refresh()
    threading.Thread(target=f, daemon=True).start()

def t_slow():
    if not ensure_cheats_gui(): return
    def f():
        state["slow"]=not state["slow"]
        if state["slow"]: state["fast"]=False
        send_cmd("host_timescale 0.3" if state["slow"] else "host_timescale 1"); refresh()
    threading.Thread(target=f, daemon=True).start()

def reset_all():
    for k in state: state[k]=False
    run_cmd("sv_cheats 0; sv_gravity 600; host_timescale 1", skip_cheats=True); refresh()

# ── Spawn ────────────────────────────────────────────────────
SPAWNS = [
    ("--- Куби ---",                    None),
    ("Companion Cube",                  "ent_create_portal_companion_cube"),
    ("Простий куб",                     "ent_create_portal_weighted_cube"),
    ("Сфера",                           "ent_create_portal_weighted_sphere"),
    ("Перенаправл. куб (лазер)",        "ent_create_portal_reflector_cube"),
    ("Куб зі старих лаб.",              "ent_create_portal_weighted_antique"),
    ("Металевий шар",                   "ent_create_portal_metal_sphere"),
    ("--- Турелі ---",                  None),
    ("Turret (ворожа)",                 "ent_create npc_portal_turret_floor"),
    ("Turret (нерухома)",               "ent_create npc_portal_turret_ground"),
    ("--- Гелі ---",                    None),
    ("Gel Bounce синій (кулька)",       "ent_create_paint_bomb_jump"),
    ("Gel Speed помаранч. (кулька)",    "ent_create_paint_bomb_speed"),
    ("Gel Reflect білий (кулька)",      "ent_create_paint_bomb_portal"),
    ("Gel Erase вода (кулька)",         "ent_create_paint_bomb_erase"),
    ("--- Energy Ball ---",             None),
    ("Energy Ball (відскакує)",         "fire_energy_ball"),
    ("--- Модулі ---",                  None),
    ("Light Bridge",                    "ent_create prop_wall_projector"),
    ("Laser Emitter",                   "ent_create env_portal_laser"),
    ("Laser Catcher",                   "ent_create prop_laser_catcher"),
    ("Laser Relay",                     "ent_create prop_laser_relay"),
    ("Excursion Funnel",                "ent_create prop_tractor_beam"),
    ("Faith Plate",                     "ent_create trigger_catapult playerspeed 600 playeronly 1"),
    ("Fizzler",                         "ent_create trigger_portal_cleanser"),
    ("Button (floor)",                  "ent_create prop_floor_button"),
    ("Button (cube)",                   "ent_create prop_floor_cube_button"),
    ("Button (weight)",                 "ent_create prop_floor_ball_button"),
    ("--- Активація модулів ---",       None),
    ("Увімк. Light Bridge",             "ent_fire prop_wall_projector Enable"),
    ("Вимк. Light Bridge",              "ent_fire prop_wall_projector Disable"),
    ("Увімк. Excursion Funnel",         "ent_fire prop_tractor_beam Enable"),
    ("Вимк. Excursion Funnel",          "ent_fire prop_tractor_beam Disable"),
    ("Увімк. Laser Emitter",            "ent_fire env_portal_laser TurnOn"),
    ("Вимк. Laser Emitter",             "ent_fire env_portal_laser TurnOff"),
    ("Натиснути всі кнопки",            "ent_fire prop_floor_button Press"),
    ("Відкрити всі двері",              "ent_fire prop_door_rotating Open"),
    ("--- Особистості / NPC ---",           None),
    ("Вітлі (prop_dynamic + анімації)",     "TWOCMD:prop_dynamic_create models/npcs/personality_sphere/personality_sphere.mdl|ent_setname prop_dynamic prt_wheatley"),
    ("Вітлі NPC (живий)",                   "npc_create npc_personality_core"),
    ("Core (NPC)",                          "npc_create npc_personality_core"),
    ("Камера спостереження",                "npc_security_camera"),
    ("Парящая турель",                      "npc_create npc_hover_turret"),
    ("Turret",                              "npc_create npc_portal_turret_floor"),
    ("Куб-турель",                          "give prop_monster_box"),
    ("--- Моделі ---",                  None),
    ("Модель Челл (P2)",                "prop_dynamic_create player/chell/player"),
    ("Модель Челл (P1 біла)",           "prop_dynamic_create player"),
    ("ERROR синій (prop)",              "ent_create prop_dynamic"),
    ("ERROR з поведінкою турелі",       "ent_create npc_turret_floor"),
    ("Ліфт з Portal 1",                 "ent_create prop_portal_stats_display"),
    ("Двері тест-камери",               "ent_create prop_testchamber_door"),
    ("--- Спец зброя ---",              None),
    ("Ракета з обличчя",                "fire_rocket_projectile"),
    ("Energy Ball (рожеві шахи)",       "fire_energy_ball"),
    ("--- Додаткові об'єкти ---",       None),
    ("Куб-туррель",                     "ent_create_portal_weight_box"),
    ("Кнопка зі старих лаб.",           "ent_create prop_under_floor_button"),
    ("--- Телепорт (коопер.) ---",      None),
    ("Телепорт Atlas (синій)",          "ent_teleport blue"),
    ("Телепорт P-body (червон.)",       "ent_teleport red"),
    ("Телепорт гравця",                 "ent_teleport !player"),
    ("Видалити всі пушки",              "ent_remove_all weapon_portalgun"),
    ("--- Видалення модулів ---",       None),
    ("Видал. Light Bridge",             "ent_fire prop_wall_projector Kill"),
    ("Видал. Funnel",                   "ent_fire prop_tractor_beam Kill"),
    ("Видал. Laser Emitter",            "ent_fire env_portal_laser Kill"),
    ("Видал. Laser Catcher",            "ent_fire prop_laser_catcher Kill"),
    ("Видал. Fizzler",                  "ent_fire trigger_portal_cleanser Kill"),
    ("Видал. Faith Plate",              "ent_fire trigger_catapult Kill"),
    ("Видал. всі кнопки",               "ent_fire prop_floor_button Kill"),
    ("--- Ще NPC ---",                      None),
    ("Камера спостереження",                "npc_security_camera"),
    ("Парящая турель",                      "npc_create npc_hover_turret"),
    ("Модуль особистості (Вітлі)",          "npc_create npc_personality_core"),
    ("--- Ще об'єкти ---",                  None),
    ("Кнопка зі старих лаб.",               "ent_create prop_under_floor_button"),
    ("Двері тест-камери",                   "ent_create prop_testchamber_door"),
    ("Ліфт з Portal 1",                     "ent_create prop_portal_stats_display"),
    ("Ракета з обличчя",                    "fire_rocket_projectile"),
    ("--- Скіни роботів (коопер.) ---",     None),
    ("Atlas: Burst (лучистий)",             "setmodel player\ballbot\ballbot_skin_burst"),
    ("Atlas: Military (камуфляж)",          "setmodel player\ballbot\ballbot_skin_military"),
    ("Atlas: Ninja (чорний)",               "setmodel player\ballbot\ballbot_skin_black"),
    ("Atlas: WCC",                          "setmodel player\ballbot\ballbot_skin_wcc"),
    ("Atlas: Moon (місяць)",                "setmodel player\ballbot\ballbot_skin_moon"),
    ("--- Очистка ---",                     None),
    ("Вбити всіх турелей",                  "ent_fire npc_portal_turret_floor Kill"),
    ("Знищити всі кубики",                  "ent_fire prop_weighted_cube Kill"),
    ("Очистити гель з підлоги",             "paint_world_clean"),
    ("Вбити всіх NPC",                      "ent_fire npc_* Kill"),
    ("Видалити всі prop_dynamic",           "ent_fire prop_dynamic Kill"),
]

# ── Misc ─────────────────────────────────────────────────────
MISC = [
    ("--- ГРАВЕЦЬ ---",                 None),
    ("Impulse 101 (всі зброї)",         "impulse 101"),
    ("Heal HP 100",                     "give item_healthkit"),
    ("Kill себе",                       "kill"),
    ("Respawn",                         "respawn_entities"),
    ("Видалити об'єкт в прицілі",       "impulse 203"),
    ("--- ПОРТАЛЬНА ПУШКА ---",         None),
    ("Give Portal Gun",                 "give_portalgun"),
    ("Upgrade Portal Gun",              "upgrade_portalgun"),
    ("Potato Gun (GLaDOS)",             "upgrade_potatogun"),
    ("Infinite portals ON",             "sv_portal_placement_never_fail 1"),
    ("Infinite portals OFF",            "sv_portal_placement_never_fail 0"),
    ("Портали круглі ON",               "portal2_square_portals 1"),
    ("Портали квадратні OFF",           "portal2_square_portals 0"),
    ("Портали крізь стіни ON",          "portal_draw_ghosting 1"),
    ("Портали крізь стіни OFF",         "portal_draw_ghosting 0"),
    ("Новий ID пушки (нові портали)",   "change_portalgun_linkage_id 1"),
    ("Розмір порталів 128x128",         "portals_resizeall 128 128"),
    ("Розмір порталів норм.",           "portals_resizeall 64 128"),
    ("--- ВИД ВІД 3-Ї ОСОБИ ---",      None),
    ("Third Person ON",                 "thirdperson"),
    ("Third Person OFF",                "firstperson"),
    ("Cam dist 150 (ближче)",           "cam_idealdist 150"),
    ("Cam dist 300 (норм.)",            "cam_idealdist 300"),
    ("Cam dist 600 (далеко)",           "cam_idealdist 600"),
    ("Cam lag 4 (норм.)",               "cam_ideallag 4"),
    ("Cam lag 100 (кінематограф)",      "cam_ideallag 100"),
    ("Cam pitch 0",                     "cam_idealpitch 0"),
    ("Cam pitch 15 (вниз)",             "cam_idealpitch 15"),
    ("Cam yaw 0",                       "cam_idealyaw 0"),
    ("Cam collision ON",                "cam_collision 1"),
    ("Cam collision OFF",               "cam_collision 0"),
    ("--- ГРАВІТАЦІЯ ---",              None),
    ("Гравітація 20 (місяць)",          "sv_gravity 20"),
    ("Гравітація 100",                  "sv_gravity 100"),
    ("Гравітація 600 (норм.)",          "sv_gravity 600"),
    ("Гравітація 2000",                 "sv_gravity 2000"),
    ("--- ФІЗИКА ---",                  None),
    ("Phys slow x0.1",                  "phys_timescale 0.1"),
    ("Phys freeze (0.001)",             "phys_timescale 0.001"),
    ("Phys норм. (1)",                  "phys_timescale 1"),
    ("--- ГРАФІКА ---",                 None),
    ("Приціл + пушка OFF",              "crosshair 0;r_drawviewmodel 0"),
    ("Приціл + пушка ON",               "crosshair 1;r_drawviewmodel 1"),
    ("Bright mode ON",                  "mat_fullbright 1"),
    ("Bright mode OFF",                 "mat_fullbright 0"),
    ("Wireframe ON",                    "mat_wireframe 1"),
    ("Wireframe OFF",                   "mat_wireframe 0"),
    ("--- ВІЗУАЛЬНІ ЕФЕКТИ ---",        None),
    ("Bloom x2",                        "mat_bloom_scalefactor_scalar 2"),
    ("Bloom x5",                        "mat_bloom_scalefactor_scalar 5"),
    ("Bloom норм. (1)",                 "mat_bloom_scalefactor_scalar 1"),
    ("Гамма авто (0)",                  "mat_force_tonemap_scale 0"),
    ("Гамма x2",                        "mat_force_tonemap_scale 2"),
    ("Ліхтарик ON/OFF",                 "impulse 100"),
    ("Neon сітка по стінах ON",         "mat_luxels 1"),
    ("Neon сітка OFF",                  "mat_luxels 0"),
    ("Зір Термінатора ON",              "mat_fillrate 1"),
    ("Зір Термінатора OFF",             "mat_fillrate 0"),
    ("Пікселі тіні ON",                 "mat_filterlightmaps 0"),
    ("Пікселі тіні OFF (норм.)",        "mat_filterlightmaps 1"),
    ("Пікс. текстури ON",               "mat_filtertextures 0"),
    ("Пікс. текстури OFF (норм.)",      "mat_filtertextures 1"),
    ("Туман екран ON",                  "mat_depthoverlay 1"),
    ("Туман екран OFF",                 "mat_depthoverlay 0"),
    ("Інверт. геометрія ON",            "mat_reversedepth 1"),
    ("Інверт. геометрія OFF",           "mat_reversedepth 0"),
    ("Розмиття (мило) ON",              "mat_fastnobump 1"),
    ("Розмиття OFF",                    "mat_fastnobump 0"),
    ("Роздільн. x0.5",                  "mat_viewportscale 0.5"),
    ("Роздільн. норм. (1)",             "mat_viewportscale 1"),
    ("Червоний фільтр +50",             "mat_ambient_light_r 50"),
    ("Синій фільтр +50",                "mat_ambient_light_g 50"),
    ("Зелений фільтр +50",              "mat_ambient_light_b 50"),
    ("Фільтри OFF (0 0 0)",             "mat_ambient_light_r 0;mat_ambient_light_g 0;mat_ambient_light_b 0"),
    ("Портал-привиди ON",               "portal_ghosts_disable 0"),
    ("Портал-привиди OFF",              "portal_ghosts_disable 1"),
    ("--- РІВЕНЬ ---",                  None),
    ("Завершити рівень",                "ent_fire @relay_finish Trigger"),
    ("Restart рівень",                  "restart_level"),
]

# ── Карти ────────────────────────────────────────────────────
MAPS = [
    ("--- Одиночна ---",         None),
    ("sp_a1_intro1",             "map sp_a1_intro1"),
    ("sp_a1_intro2",             "map sp_a1_intro2"),
    ("sp_a1_intro3",             "map sp_a1_intro3"),
    ("sp_a1_intro4",             "map sp_a1_intro4"),
    ("sp_a1_intro5",             "map sp_a1_intro5"),
    ("sp_a1_intro6",             "map sp_a1_intro6"),
    ("sp_a1_intro7",             "map sp_a1_intro7"),
    ("sp_a1_wakeup",             "map sp_a1_wakeup"),
    ("sp_a2_intro",              "map sp_a2_intro"),
    ("sp_a2_laser_intro",        "map sp_a2_laser_intro"),
    ("sp_a2_laser_stairs",       "map sp_a2_laser_stairs"),
    ("sp_a2_dual_lasers",        "map sp_a2_dual_lasers"),
    ("sp_a2_laser_over_goo",     "map sp_a2_laser_over_goo"),
    ("sp_a2_catapult_intro",     "map sp_a2_catapult_intro"),
    ("sp_a2_trust_fling",        "map sp_a2_trust_fling"),
    ("sp_a2_pit_flings",         "map sp_a2_pit_flings"),
    ("sp_a2_fizzler_intro",      "map sp_a2_fizzler_intro"),
    ("sp_a2_sphere_peek",        "map sp_a2_sphere_peek"),
    ("sp_a2_ricochet",           "map sp_a2_ricochet"),
    ("sp_a2_bridge_intro",       "map sp_a2_bridge_intro"),
    ("sp_a2_bridge_the_gap",     "map sp_a2_bridge_the_gap"),
    ("sp_a2_turret_intro",       "map sp_a2_turret_intro"),
    ("sp_a2_turret_blocker",     "map sp_a2_turret_blocker"),
    ("sp_a2_turret_lookout",     "map sp_a2_turret_lookout"),
    ("sp_a2_bts1",               "map sp_a2_bts1"),
    ("sp_a2_bts2",               "map sp_a2_bts2"),
    ("sp_a2_bts3",               "map sp_a2_bts3"),
    ("sp_a2_bts4",               "map sp_a2_bts4"),
    ("sp_a2_bts5",               "map sp_a2_bts5"),
    ("sp_a2_bts6",               "map sp_a2_bts6"),
    ("sp_a2_core",               "map sp_a2_core"),
    ("sp_a3_00",                 "map sp_a3_00"),
    ("sp_a3_01",                 "map sp_a3_01"),
    ("sp_a3_03",                 "map sp_a3_03"),
    ("sp_a3_jump_intro",         "map sp_a3_jump_intro"),
    ("sp_a3_bomb_flings",        "map sp_a3_bomb_flings"),
    ("sp_a3_crazy_box",          "map sp_a3_crazy_box"),
    ("sp_a3_transition01",       "map sp_a3_transition01"),
    ("sp_a4_intro",              "map sp_a4_intro"),
    ("sp_a4_tb_intro",           "map sp_a4_tb_intro"),
    ("sp_a4_tb_trust_drop",      "map sp_a4_tb_trust_drop"),
    ("sp_a4_tb_wall_button",     "map sp_a4_tb_wall_button"),
    ("sp_a4_tb_polarity",        "map sp_a4_tb_polarity"),
    ("sp_a4_tb_catch",           "map sp_a4_tb_catch"),
    ("sp_a4_tb_laser_catapult",  "map sp_a4_tb_laser_catapult"),
    ("sp_a4_tb_laser_platform",  "map sp_a4_tb_laser_platform"),
    ("sp_a4_tb_dimensions",      "map sp_a4_tb_dimensions"),
    ("sp_a4_finale1",            "map sp_a4_finale1"),
    ("sp_a4_finale2",            "map sp_a4_finale2"),
    ("sp_a4_finale3",            "map sp_a4_finale3"),
    ("sp_a4_finale4",            "map sp_a4_finale4"),
]

# ── Вікна ────────────────────────────────────────────────────
def get_all_windows():
    results = []
    def cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            t = win32gui.GetWindowText(hwnd)
            if t.strip(): results.append((t, hwnd))
    win32gui.EnumWindows(cb, None)
    return sorted(results, key=lambda x: x[0].lower())

# ════════════════════════════════════════════════════════════
# GUI
# ════════════════════════════════════════════════════════════
BG="#0b0e14"; BG2="#0d1219"; BORDER="#1a2540"
ACCENT="#00aaff"; ACCENT2="#ff6600"; TEXT_DIM="#3a4a6a"
ON_CLR="#00ff88"; OFF_CLR="#1a2535"; OFF_TXT="#5070a0"
TAB_ACT="#0d2035"; TAB_IN="#090d14"
HDR_CLR="#ffcc00"

root = tk.Tk()
root.title("PRT MENU")
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-alpha", 0.95)
root.configure(bg=BG)
root.geometry("280x660+40+40")

_d={"x":0,"y":0}
def sd(e): _d["x"]=e.x; _d["y"]=e.y
def dd(e): root.geometry(f"+{root.winfo_x()+e.x-_d['x']}+{root.winfo_y()+e.y-_d['y']}")

# Header
hdr=tk.Frame(root,bg=BG2,cursor="fleur"); hdr.pack(fill="x")
hdr.bind("<ButtonPress-1>",sd); hdr.bind("<B1-Motion>",dd)
tk.Label(hdr,text="◈ PRT MENU",font=("Courier New",10,"bold"),bg=BG2,fg=ACCENT,pady=7).pack(side="left",padx=10)
xb=tk.Label(hdr,text="✕",font=("Courier New",11),bg=BG2,fg=TEXT_DIM,cursor="hand2",padx=10)
xb.pack(side="right")
xb.bind("<Button-1>",lambda e:root.destroy())
xb.bind("<Enter>",lambda e:xb.config(fg="#ff4444"))
xb.bind("<Leave>",lambda e:xb.config(fg=TEXT_DIM))
tk.Frame(root,bg=BORDER,height=1).pack(fill="x")

# Процес
pf=tk.Frame(root,bg=BG,padx=8,pady=5); pf.pack(fill="x")
tk.Label(pf,text="ПРОЦЕС",font=("Courier New",7,"bold"),bg=BG,fg=TEXT_DIM).pack(anchor="w")
sf=tk.Frame(pf,bg=BG); sf.pack(fill="x",pady=(2,0))
proc_var=tk.StringVar(value="-- вибери вікно --")
combo=ttk.Combobox(sf,textvariable=proc_var,font=("Courier New",8),state="readonly",width=24)
combo.pack(side="left",fill="x",expand=True)
status=tk.Label(pf,text="● не вибрано",font=("Courier New",7),bg=BG,fg="#ff4444")
status.pack(anchor="w",pady=(2,0))

def refresh_wins():
    global wins_map
    wins=get_all_windows(); wins_map={t:h for t,h in wins}
    names=[t for t,h in wins]
    p2=[n for n in names if "portal" in n.lower()]
    other=[n for n in names if n not in p2]
    combo["values"]=p2+other
    if p2 and not target_hwnd:
        proc_var.set(p2[0]); select_win(p2[0])

def select_win(title=None):
    global target_hwnd
    t=title or proc_var.get()
    if t in wins_map:
        target_hwnd=wins_map[t]
        status.config(text=f"● {t[:32]}",fg=ON_CLR)
    else:
        target_hwnd=None; status.config(text="● не знайдено",fg="#ff4444")

combo.bind("<<ComboboxSelected>>",lambda e:select_win())
rb=tk.Button(sf,text="⟳",font=("Courier New",9,"bold"),bg=BORDER,fg=ACCENT,
             activebackground="#1a3a5a",activeforeground="#fff",
             relief="flat",bd=0,cursor="hand2",padx=6,command=refresh_wins)
rb.pack(side="right",padx=(4,0))
tk.Frame(root,bg=BORDER,height=1).pack(fill="x")

# Autoexec
af=tk.Frame(root,bg=BG,padx=8,pady=4); af.pack(fill="x")
ae=tk.Button(af,text="▶  EXEC AUTOEXEC",font=("Courier New",9,"bold"),
             bg="#0a1a2a",fg="#00ccff",activebackground="#0d3050",activeforeground="#fff",
             relief="flat",bd=0,cursor="hand2",pady=5,
             command=lambda:run_cmd("exec autoexec",skip_cheats=True))
ae.pack(fill="x")
ae.bind("<Enter>",lambda e:ae.config(bg="#0d2a40"))
ae.bind("<Leave>",lambda e:ae.config(bg="#0a1a2a"))
tk.Frame(root,bg=BORDER,height=1).pack(fill="x")

tk.Label(root,text="Insert = сховати / показати",
         font=("Courier New",6),bg=BG,fg=TEXT_DIM,pady=2).pack()
tk.Frame(root,bg=BORDER,height=1).pack(fill="x")

# ── Таби ─────────────────────────────────────────────────────
tab_bar=tk.Frame(root,bg=BG2); tab_bar.pack(fill="x")
content_frame=tk.Frame(root,bg=BG); content_frame.pack(fill="both",expand=True)
tk.Frame(root,bg=BORDER,height=1).pack(fill="x")
tk.Label(root,text="тягни за заголовок",font=("Courier New",6),bg=BG,fg=TEXT_DIM,pady=2).pack()

pages={}; tab_btns={}; active_tab=[None]

def switch_tab(name):
    if active_tab[0]: pages[active_tab[0]].pack_forget()
    pages[name].pack(fill="both",expand=True)
    active_tab[0]=name
    for n,b in tab_btns.items():
        b.config(bg=TAB_ACT if n==name else TAB_IN,
                 fg=ACCENT if n==name else OFF_TXT)

for tab_name in ["CHEATS","SPAWN","MISC","MAPS","BIND"]:
    p=tk.Frame(content_frame,bg=BG); pages[tab_name]=p
    b=tk.Button(tab_bar,text=tab_name,font=("Courier New",7,"bold"),
                bg=TAB_IN,fg=OFF_TXT,relief="flat",bd=0,
                cursor="hand2",pady=5,padx=4,
                command=lambda n=tab_name: switch_tab(n))
    b.pack(side="left",fill="x",expand=True)
    tab_btns[tab_name]=b

# ════════ CHEATS ════════
cp=pages["CHEATS"]
widgets={}
TOGGLE_BTNS=[
    ("sv_cheats",  "SV_CHEATS",    toggle_cheats,  ACCENT),
    ("noclip",     "NOCLIP",       t_noclip,       ACCENT),
    ("god",        "GOD MODE",     t_god,          ON_CLR),
    ("buddha",     "BUDDHA",       t_buddha,       ON_CLR),
    ("notarget",   "NOTARGET",     t_notarget,     "#ffcc00"),
    ("thirdperson","3RD PERSON",   t_thirdperson,  "#ffcc00"),
    ("fly",        "LOW GRAVITY",  t_fly,          "#ffcc00"),
    ("fast",       "FAST  x3",     t_fast,         ACCENT2),
    ("slow",       "SLOW x0.3",    t_slow,         ACCENT2),
]
scr_c=tk.Frame(cp,bg=BG); scr_c.pack(fill="both",expand=True,padx=8,pady=4)
for key,label,cmd,accent in TOGGLE_BTNS:
    row=tk.Frame(scr_c,bg=BG,pady=2); row.pack(fill="x")
    dot=tk.Label(row,text="●",font=("Courier New",8),bg=BG,fg=OFF_CLR,width=2); dot.pack(side="left")
    btn=tk.Button(row,text=label,font=("Courier New",9,"bold"),
                  bg=OFF_CLR,fg=OFF_TXT,activebackground=accent,activeforeground="#000",
                  relief="flat",bd=0,cursor="hand2",width=14,pady=4,command=cmd)
    btn.pack(side="left",fill="x",expand=True)
    lbl=tk.Label(row,text="OFF",font=("Courier New",7),bg=BG,fg=OFF_CLR,width=4); lbl.pack(side="right")
    widgets[key]=(btn,dot,lbl,accent)
tk.Frame(scr_c,bg=BORDER,height=1).pack(fill="x",pady=3)
rst=tk.Button(scr_c,text="⟳  RESET ALL",font=("Courier New",9,"bold"),
              bg="#200808",fg="#ff5555",activebackground="#ff3333",activeforeground="#000",
              relief="flat",bd=0,cursor="hand2",pady=4,command=reset_all)
rst.pack(fill="x")
rst.bind("<Enter>",lambda e:rst.config(bg="#3a0808"))
rst.bind("<Leave>",lambda e:rst.config(bg="#200808"))

# ════════ SPAWN ════════
sp=pages["SPAWN"]
tk.Label(sp,text="Спавн об'єктів поруч з тобою",font=("Courier New",7),bg=BG,fg=TEXT_DIM,pady=3).pack()
tk.Frame(sp,bg=BORDER,height=1).pack(fill="x",padx=8)

sp_canvas=tk.Canvas(sp,bg=BG,highlightthickness=0)
sp_scroll=ttk.Scrollbar(sp,orient="vertical",command=sp_canvas.yview)
sp_canvas.configure(yscrollcommand=sp_scroll.set)
sp_scroll.pack(side="right",fill="y")
sp_canvas.pack(side="left",fill="both",expand=True)
sp_inner=tk.Frame(sp_canvas,bg=BG)
sp_canvas.create_window((0,0),window=sp_inner,anchor="nw")
sp_inner.bind("<Configure>",lambda e:sp_canvas.configure(scrollregion=sp_canvas.bbox("all")))
sp_canvas.bind("<MouseWheel>",lambda e:sp_canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

for label,cmd in SPAWNS:
    if cmd is None:
        lbl=tk.Label(sp_inner,text=label,font=("Courier New",7,"bold"),
                     bg=BG,fg=HDR_CLR,pady=2,padx=10,anchor="w")
        lbl.pack(fill="x",padx=8)
    else:
        btn=tk.Button(sp_inner,text=label,font=("Courier New",9,"bold"),
                      bg=OFF_CLR,fg="#88aaff",activebackground="#1a3a6a",activeforeground="#fff",
                      relief="flat",bd=0,cursor="hand2",pady=5,anchor="w",padx=10,width=28,
                      command=lambda c=cmd:(run_two_cmds(*c[8:].split("|")) if c.startswith("TWOCMD:") else run_cmd(c)))
        btn.pack(fill="x",pady=2,padx=8)
        btn.bind("<Enter>",lambda e,b=btn:b.config(bg="#1a2a40"))
        btn.bind("<Leave>",lambda e,b=btn:b.config(bg=OFF_CLR))

# ════════ MISC ════════
mp=pages["MISC"]

# Пошук
search_misc=tk.StringVar()
sf2=tk.Frame(mp,bg=BG,padx=8,pady=4); sf2.pack(fill="x")
tk.Label(sf2,text="🔍",font=("Courier New",10),bg=BG,fg=TEXT_DIM).pack(side="left")
se2=tk.Entry(sf2,textvariable=search_misc,font=("Courier New",9),bg=OFF_CLR,
             fg="#aaccff",insertbackground="#aaccff",relief="flat",bd=0)
se2.pack(side="left",fill="x",expand=True,padx=4)
tk.Frame(mp,bg=BORDER,height=1).pack(fill="x",padx=8)

misc_canvas=tk.Canvas(mp,bg=BG,highlightthickness=0)
misc_scroll=ttk.Scrollbar(mp,orient="vertical",command=misc_canvas.yview)
misc_canvas.configure(yscrollcommand=misc_scroll.set)
misc_scroll.pack(side="right",fill="y")
misc_canvas.pack(side="left",fill="both",expand=True)
misc_inner=tk.Frame(misc_canvas,bg=BG)
misc_canvas.create_window((0,0),window=misc_inner,anchor="nw")
misc_inner.bind("<Configure>",lambda e:misc_canvas.configure(scrollregion=misc_canvas.bbox("all")))
misc_canvas.bind("<MouseWheel>",lambda e:misc_canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

misc_btn_list=[]
for label,cmd in MISC:
    if cmd is None:
        lbl=tk.Label(misc_inner,text=label,font=("Courier New",7,"bold"),
                     bg=BG,fg=HDR_CLR,pady=2,padx=10,anchor="w")
        lbl.pack(fill="x",padx=8)
        misc_btn_list.append((lbl,label,None))
    else:
        btn=tk.Button(misc_inner,text=label,font=("Courier New",9,"bold"),
                      bg=OFF_CLR,fg="#ffaa55",activebackground="#2a1a05",activeforeground="#fff",
                      relief="flat",bd=0,cursor="hand2",pady=4,anchor="w",padx=10,width=28,
                      command=lambda c=cmd:run_cmd(c))
        btn.pack(fill="x",pady=1,padx=8)
        btn.bind("<Enter>",lambda e,b=btn:b.config(bg="#1a1205"))
        btn.bind("<Leave>",lambda e,b=btn:b.config(bg=OFF_CLR))
        misc_btn_list.append((btn,label,cmd))

def filter_misc(*args):
    q=search_misc.get().lower()
    for widget,label,cmd in misc_btn_list:
        if not q or q in label.lower():
            widget.pack(fill="x",pady=(0 if cmd is None else 1),padx=8)
        else:
            widget.pack_forget()
    misc_canvas.configure(scrollregion=misc_canvas.bbox("all"))
search_misc.trace("w",filter_misc)

# ════════ MAPS ════════
mapp=pages["MAPS"]
search_map=tk.StringVar()
sf3=tk.Frame(mapp,bg=BG,padx=8,pady=4); sf3.pack(fill="x")
tk.Label(sf3,text="🔍",font=("Courier New",10),bg=BG,fg=TEXT_DIM).pack(side="left")
se3=tk.Entry(sf3,textvariable=search_map,font=("Courier New",9),bg=OFF_CLR,
             fg="#aaccff",insertbackground="#aaccff",relief="flat",bd=0)
se3.pack(side="left",fill="x",expand=True,padx=4)
tk.Frame(mapp,bg=BORDER,height=1).pack(fill="x",padx=8)

map_canvas=tk.Canvas(mapp,bg=BG,highlightthickness=0)
map_scroll=ttk.Scrollbar(mapp,orient="vertical",command=map_canvas.yview)
map_canvas.configure(yscrollcommand=map_scroll.set)
map_scroll.pack(side="right",fill="y")
map_canvas.pack(side="left",fill="both",expand=True)
map_inner=tk.Frame(map_canvas,bg=BG)
map_canvas.create_window((0,0),window=map_inner,anchor="nw")
map_inner.bind("<Configure>",lambda e:map_canvas.configure(scrollregion=map_canvas.bbox("all")))
map_canvas.bind("<MouseWheel>",lambda e:map_canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

map_btn_list=[]
for label,cmd in MAPS:
    if cmd is None:
        lbl=tk.Label(map_inner,text=label,font=("Courier New",7,"bold"),
                     bg=BG,fg=HDR_CLR,pady=2,padx=10,anchor="w")
        lbl.pack(fill="x",padx=8)
        map_btn_list.append((lbl,label,None))
    else:
        btn=tk.Button(map_inner,text=label,font=("Courier New",9,"bold"),
                      bg=OFF_CLR,fg="#aaffcc",activebackground="#0a2a1a",activeforeground="#fff",
                      relief="flat",bd=0,cursor="hand2",pady=4,anchor="w",padx=10,width=28,
                      command=lambda c=cmd:run_cmd(c,skip_cheats=True))
        btn.pack(fill="x",pady=1,padx=8)
        btn.bind("<Enter>",lambda e,b=btn:b.config(bg="#0d1f14"))
        btn.bind("<Leave>",lambda e,b=btn:b.config(bg=OFF_CLR))
        map_btn_list.append((btn,label,cmd))

def filter_map(*args):
    q=search_map.get().lower()
    for widget,label,cmd in map_btn_list:
        if not q or q in label.lower():
            widget.pack(fill="x",pady=(0 if cmd is None else 1),padx=8)
        else:
            widget.pack_forget()
    map_canvas.configure(scrollregion=map_canvas.bbox("all"))
search_map.trace("w",filter_map)

# ════════ BIND ════════
bp=pages["BIND"]
tk.Label(bp,text="Bind клавіші до команди",font=("Courier New",8,"bold"),
         bg=BG,fg=ACCENT,pady=6).pack()
tk.Frame(bp,bg=BORDER,height=1).pack(fill="x",padx=8)

bf=tk.Frame(bp,bg=BG,padx=12,pady=8); bf.pack(fill="x")

tk.Label(bf,text="Клавіша (напр. f5, k, mouse3):",
         font=("Courier New",8),bg=BG,fg=TEXT_DIM).pack(anchor="w")
key_var=tk.StringVar()
key_entry=tk.Entry(bf,textvariable=key_var,font=("Courier New",10),
                   bg=OFF_CLR,fg="#fff",insertbackground="#fff",
                   relief="flat",bd=0,width=20)
key_entry.pack(fill="x",pady=(2,8),ipady=4)

tk.Label(bf,text="Команда (напр. noclip, god):",
         font=("Courier New",8),bg=BG,fg=TEXT_DIM).pack(anchor="w")
cmd_var=tk.StringVar()
cmd_entry=tk.Entry(bf,textvariable=cmd_var,font=("Courier New",10),
                   bg=OFF_CLR,fg="#fff",insertbackground="#fff",
                   relief="flat",bd=0,width=20)
cmd_entry.pack(fill="x",pady=(2,8),ipady=4)

bind_status=tk.Label(bf,text="",font=("Courier New",8),bg=BG,fg=ON_CLR)
bind_status.pack(anchor="w")

# Швидкий вибір команди
tk.Label(bf,text="Швидкий вибір команди:",
         font=("Courier New",7),bg=BG,fg=TEXT_DIM).pack(anchor="w",pady=(4,0))
quick_cmds=["noclip","god","buddha","kill","impulse 101",
            "sv_cheats 1","sv_cheats 0","notarget",
            "thirdperson","firstperson","sv_gravity 100","sv_gravity 600"]
qf=tk.Frame(bf,bg=BG); qf.pack(fill="x",pady=(2,0))
for i,qc in enumerate(quick_cmds):
    b=tk.Button(qf,text=qc,font=("Courier New",7),
                bg=BORDER,fg="#aaccff",activebackground=TAB_ACT,activeforeground="#fff",
                relief="flat",bd=0,cursor="hand2",padx=4,pady=2,
                command=lambda c=qc:cmd_var.set(c))
    b.grid(row=i//2,column=i%2,sticky="ew",padx=2,pady=1)
qf.columnconfigure(0,weight=1); qf.columnconfigure(1,weight=1)

def do_bind():
    k=key_var.get().strip()
    c=cmd_var.get().strip()
    if not k or not c:
        bind_status.config(text="Заповни обидва поля!",fg="#ff5555"); return
    # Конвертуємо укр → eng
    k_en=ua_to_en(k)
    if k_en!=k:
        bind_status.config(text=f"Укр клавіша '{k}' → '{k_en}'",fg="#ffcc00")
        root.after(1500,lambda:do_bind_send(k_en,c))
    else:
        do_bind_send(k,c)

def do_bind_send(k,c):
    final_cmd=f"bind {k} {c}"
    bind_status.config(text=f"Відправлено: {final_cmd}",fg=ON_CLR)
    run_cmd(final_cmd)

bind_btn=tk.Button(bf,text="🔗  ЗРОБИТИ BIND",font=("Courier New",9,"bold"),
                   bg="#0a2a0a",fg=ON_CLR,activebackground="#0d4a0d",activeforeground="#fff",
                   relief="flat",bd=0,cursor="hand2",pady=7,command=do_bind)
bind_btn.pack(fill="x",pady=(10,2))
bind_btn.bind("<Enter>",lambda e:bind_btn.config(bg="#0d3a0d"))
bind_btn.bind("<Leave>",lambda e:bind_btn.config(bg="#0a2a0a"))

tk.Label(bf,text="Unbind: вбери cmd поле і напиши unbind KEY",
         font=("Courier New",6),bg=BG,fg=TEXT_DIM,wraplength=200,justify="left").pack(anchor="w",pady=4)


# Активувати перший таб
switch_tab("CHEATS")

def refresh():
    for key,(btn,dot,lbl,accent) in widgets.items():
        on=state.get(key,False)
        btn.config(bg=accent if on else OFF_CLR,fg="#000" if on else OFF_TXT)
        dot.config(fg=accent if on else OFF_CLR)
        lbl.config(text="ON" if on else "OFF",fg=accent if on else OFF_CLR)

refresh()

style=ttk.Style(); style.theme_use("clam")
style.configure("TCombobox",fieldbackground=OFF_CLR,background=BORDER,
                foreground="#aaccff",selectbackground=BORDER,selectforeground="#fff",borderwidth=0)
style.configure("Vertical.TScrollbar",background=BORDER,troughcolor=BG,
                arrowcolor=TEXT_DIM,borderwidth=0)

vis=[True]
def show_menu():
    root.deiconify(); root.attributes("-topmost",True)
    root.focus_force(); release_mouse(); vis[0]=True

def hide_menu():
    root.withdraw()
    if target_hwnd:
        try:
            win32gui.ShowWindow(target_hwnd,9)
            win32gui.SetForegroundWindow(target_hwnd)
        except: pass
    vis[0]=False

def toggle_vis():
    if vis[0]: hide_menu()
    else: show_menu()

try: keyboard.add_hotkey("insert",toggle_vis)
except: pass

root.after(600,refresh_wins)
root.after(800,release_mouse)
print("PRT MENU запущено! Insert = сховати/показати")
root.mainloop()
