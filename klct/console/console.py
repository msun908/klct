# -*- coding: utf-8 -*-
import curses
import locale
import sys
sys.path.insert(0, '../ldap')
import configTool


locale.setlocale(locale.LC_ALL,"")
term_screen = curses.initscr()  # terminal screen
term_screen_dimensions = term_screen.getmaxyx()
term_screen.keypad(True)
curses.noecho()
start_instruction = "LDAP Configuration Tool. Press 'm' to go to the menu."

if curses.has_colors():
    curses.start_color()

curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
curses.init_pair(2, curses.COLOR_MAGENTA, curses.COLOR_WHITE)
curses.init_pair(3, curses.COLOR_RED, curses.COLOR_WHITE)
curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)
curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_WHITE)
term_screen.bkgd(curses.color_pair(1))

check_list = ['☐'] * 12
menu_options = ["Ping LDAP Server IP",
                "Check Connection to LDAP Server",
                "Get Server Information",
                "Check LDAP Suffix",
                "Show List of User-Related ObjectClasses",
                "Check User Tree DN and Show List of Users",
                "Get a Specific User",
                "Show List of Group Related ObjectClasses",
                "Check Group Tree DN and Show List of Groups",
                "Get Specific Group",
                "Add Additional Configuration Options",
                "Show Configuration",
                "Save/Create Configuration File"]


def show_instructions(screen):
    curses.curs_set(0)
    screen_dimensions = screen.getmaxyx()
    screen.clear()
    char_press = 0
    screen.addstr(screen_dimensions[0]/2,
                  screen_dimensions[1]/2 - len(start_instruction)/2, start_instruction)
    while char_press != ord('m'):
        char_press = screen.getch()
    display_menu(screen)


def menu_ping_ldap_ip(screen):
    success = "Successfully pinged given IP address."
    fail = "Unsuccessfully pinged given IP address."
    screen.clear()
    temp_char = 0
    screen_dims = screen.getmaxyx()
    ip_string = my_raw_input(screen, screen_dims[0]/2, screen_dims[1]/2 - 23,
                             "Please Enter the IP Address of the LDAP server.")
    temp_bool = configTool.ping_LDAP_server(ip_string)  # change to boolean value

    if temp_bool == 0:
        screen.addstr(screen_dims[0]/2 + 4, screen_dims[1]/2 - len(success)/2, success)
        screen.addstr(screen_dims[0]/2 + 5, screen_dims[1]/2 - 25,
                      "Press 'n' to move on to next step, or 'm' for menu.")
        menu_options[0] = u"Ping LDAP Server IP ✓"
    else:
        screen.addstr(screen_dims[0]/2 + 4, screen_dims[1]/2 - len(fail) / 2, fail)
        screen.addstr(screen_dims[0]/2 + 5, screen_dims[1]/2 - 18,
                      "Press 'r' to retry, or 'm' for menu.")

    while temp_char not in (110, 109, 114):  # 109 = 'm', 110 = 'n', 114 = 'r'
        temp_char = screen.getch()
    if temp_char == 109:
        display_menu(screen)
    elif temp_char == 110:
        print("TEMP, MOVE ON TO NEXT METHOD CALL")
    elif temp_char == 114:
        menu_ping_ldap_ip(screen)


def my_raw_input(screen, y, x, prompt_string):
    curses.echo()
    screen.addstr(y, x, prompt_string, curses.color_pair(2))
    screen.addch(y + 1, x, ">")
    screen.refresh()
    str_input = screen.getstr(y + 1, x + 1, 20)
    curses.noecho()
    return str_input


def display_menu(screen):
    screen_dimensions = screen.getmaxyx()
    screen_half_y = screen_dimensions[0]/2
    screen_half_x = screen_dimensions[1]/2
    screen.nodelay(0)
    screen.clear()
    menu_selection = -1
    option_num = 0
    while menu_selection < 0:
        menu_highlighting = [0] * 13
        menu_highlighting[option_num] = curses.A_STANDOUT
        screen.addstr(0, screen_half_x - 11,
                      "LDAP Configuration Menu",curses.A_UNDERLINE | curses.color_pair(1) | curses.A_BOLD)
        screen.addstr(screen_half_y - 6, screen_half_x - len(menu_options[0])/2,
                      (menu_options[0]).encode("utf-8"), menu_highlighting[0] | curses.color_pair(2))
        screen.addstr(screen_half_y - 5, screen_half_x - len(menu_options[1])/2,
                      menu_options[1], menu_highlighting[1] | curses.color_pair(2))
        screen.addstr(screen_half_y - 4, screen_half_x - len(menu_options[2])/2,
                      menu_options[2], menu_highlighting[2] | curses.color_pair(2))
        screen.addstr(screen_half_y - 3, screen_half_x - len(menu_options[3])/2,
                      menu_options[3], menu_highlighting[3] | curses.color_pair(2))
        screen.addstr(screen_half_y - 2, screen_half_x - len(menu_options[4])/2,
                      menu_options[4], menu_highlighting[4] | curses.color_pair(2))
        screen.addstr(screen_half_y - 1, screen_half_x - len(menu_options[5])/2,
                      menu_options[5], menu_highlighting[5] | curses.color_pair(2))
        screen.addstr(screen_half_y + 0, screen_half_x - len(menu_options[6])/2,
                      menu_options[6], menu_highlighting[6] | curses.color_pair(2))
        screen.addstr(screen_half_y + 1, screen_half_x - len(menu_options[7])/2,
                      menu_options[7], menu_highlighting[7] | curses.color_pair(2))
        screen.addstr(screen_half_y + 2, screen_half_x - len(menu_options[8])/2,
                      menu_options[8], menu_highlighting[8] | curses.color_pair(2))
        screen.addstr(screen_half_y + 3, screen_half_x - len(menu_options[9])/2,
                      menu_options[9], menu_highlighting[9] | curses.color_pair(2))
        screen.addstr(screen_half_y + 4, screen_half_x - len(menu_options[10])/2,
                      menu_options[10], menu_highlighting[10] | curses.color_pair(2))
        screen.addstr(screen_half_y + 5, screen_half_x - len(menu_options[11])/2,
                      menu_options[11], menu_highlighting[11] | curses.color_pair(2))
        screen.addstr(screen_half_y + 6, screen_half_x - 2, "Exit", menu_highlighting[12] | curses.color_pair(3))
        screen.refresh()

        key_press = screen.getch()
        if key_press == curses.KEY_UP:
            option_num = (option_num - 1) % 13
        elif key_press == curses.KEY_DOWN:
            option_num = (option_num + 1) % 13
        elif key_press == ord('\n'):
            menu_selection = option_num
            if option_num == 0:
                menu_ping_ldap_ip(screen)

    curses.curs_set(1)

curses.wrapper(show_instructions)
curses.endwin()
