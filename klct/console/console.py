# -*- coding: utf-8 -*-
import curses
import locale
import os.path
import sys
import yaml
sys.path.insert(0, '../ldap')
import configTool


"""SET UP"""
locale.setlocale(locale.LC_ALL, "")  # for unicode support
term_screen = curses.initscr()  # terminal screen
term_screen_dimensions = term_screen.getmaxyx()  # returns tuple (y,x) of current screen resolution
term_screen.keypad(True)  # enables arrow keys and multi-byte sequences i.e.(f1-f12,page up, page down)
curses.noecho()
start_instruction = "LDAP Configuration Tool. Press 'm' to go to the menu."
if curses.has_colors():  # enable coloring
    curses.start_color()
curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
curses.init_pair(2, curses.COLOR_MAGENTA, curses.COLOR_WHITE)
curses.init_pair(3, curses.COLOR_RED, curses.COLOR_WHITE)
curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_WHITE)
curses.init_pair(6, curses.COLOR_GREEN, curses.COLOR_BLACK)
curses.init_pair(7, curses.COLOR_GREEN, curses.COLOR_WHITE)
term_screen.bkgd(curses.color_pair(1))
"""Configuration File Status Windows, one for box and one for displaying text"""
status_window = term_screen.subwin(term_screen_dimensions[0] - 2, term_screen_dimensions[1] / 4 - 2, 1,
                                   term_screen_dimensions[1] - term_screen_dimensions[1]/4 )
status_window_text = term_screen.subwin(term_screen_dimensions[0] - 4, term_screen_dimensions[1] / 4 - 4, 2,
                                        term_screen_dimensions[1] - term_screen_dimensions[1]/4 + 1)

"""VARS THAT MIGHT CHANGE DURING EXECUTION OF PROGRAM"""
menu_color = [curses.color_pair(2)] * 14  # number of menu options = 12
menu_options = ["1. Enter/Validate LDAP Server IP",
                "2. Check Connection to LDAP Server (URL)",
                "3. Check Connection to LDAP Server (URL,User/Pass,SSL/TLS)",
                "4. Get Server Information",
                "5. Check LDAP Suffix",
                "6. Show List of User-Related ObjectClasses",
                "7. Check User Tree DN and Show List of Users",
                "8. Get a Specific User",
                "9. Show List of Group Related ObjectClasses",
                "10. Check Group Tree DN and Show List of Groups",
                "11. Get Specific Group",
                "12. Add Additional Configuration Options",
                "13. Show Configuration",
                "14. Save/Create Configuration File"]
configuration_dict = {"url": "none",
                      "suffix": "none",
                      "query_scope": "none",
                      "user_tree_dn": "none",
                      "user": "none",
                      "password": "none",
                      "user_object_class": "none",
                      "user_id_attribute": "none",
                      "user_name_attribute": "none",
                      "group_tree_dn":"none",
                      "group_objectclass": "none",
                      "group_id_attribute": "none",
                      "use_pool": "none",
                      "user_enabled_attribute": "none",
                      "user_enabled_mask": "none",
                      "user_enabled_default": "none",
                      "use_tls": "none"
               }
var_dict = {"conn_info": "none"}

"""HELPER METHODS"""


def show_instructions(screen):
    """Displays the starting instructions prior to the menu display."""
    curses.curs_set(0)
    screen_dimensions = screen.getmaxyx()
    screen.clear()
    char_press = 0
    screen.addstr(screen_dimensions[0]/2,
                  screen_dimensions[1]/2 - len(start_instruction)/2, start_instruction)
    while char_press != ord('m'):
        char_press = screen.getch()
    screen.clear()
    screen.box()
    screen.refresh()
    main_window = screen.subwin(screen_dimensions[0] - 2, screen_dimensions[1] - screen_dimensions[1]/4 - 1, 1, 1)
    main_window.keypad(True)
    display_menu(main_window, status_window)


def my_raw_input(screen, y, x, prompt_string):
    """Prompt for input from user. Given a (y, x) coordinate,
    will show a prompt at (y + 1, x). Currently only able to
    prompt for 20 chars, but can change later."""
    curses.echo() # so user can see
    screen.addstr(y, x, prompt_string, curses.color_pair(2))
    screen.addch(y + 1, x, ">")
    screen.refresh()
    str_input = screen.getstr(y + 1, x + 1, 30)  # 20 = max chars to in string
    curses.noecho()
    return str_input


def my_pw_input(screen, y, x, prompt_string):
    """Prompt for input from user. Given a (y, x) coordinate,
    will show a prompt at (y + 1, x). Will echo characters but as an '*',
    to hide the password's characters from showing on the screen."""
    curses.noecho() # no echoing
    screen.addstr(y, x, prompt_string, curses.color_pair(2))
    screen.addch(y + 1, x, ">")
    screen.refresh()
    x_coord = x + 1
    str_input_pos = 0
    c = screen.getch()
    str_input = []
    while c != 10:
        if c < 256:
            str_input.append(chr(c))
            screen.addch(y + 1, x_coord, "*")
            x_coord += 1
            str_input_pos += 1
        c = screen.getch()
        if c in (263, 8, 330):
            if x_coord > x + 1:
                x_coord -= 1
            screen.addch(y + 1, x_coord, " ")
            if str_input_pos > 0:
                str_input_pos -= 1
            if len(str_input) > 0:
                str_input.pop()
    pw_input = ''.join(str_input)
    return pw_input


def prompt_char_input(screen, y, x, prompt_string, list):
    """Prompt for a single character input from user until user gives a char in list.
     Given a (y, x) coordinate, will show a prompt at (y + 1, x)."""
    curses.echo() # no echoing
    screen.addstr(y, x, prompt_string, curses.color_pair(2))
    screen.addch(y + 1, x, ">")
    screen.refresh()
    ch_input = screen.getstr(y + 1, x + 1, 1)  # 20 = max chars to in string
    while ch_input not in list:
        screen.addstr(y, x, "                                     ")
        screen.addstr(y + 1, x, "> ")
        screen.addstr(y, x, prompt_string, curses.color_pair(2))
        screen.refresh()
        ch_input = screen.getstr(y + 1, x + 1, 1)
    return ch_input


def setup_menu_call(screen):
    """Typically called at start of a menu method.
    Clears screen and returns max y and max x in tuple (max_y, max_x)."""
    screen.clear()
    return screen.getmaxyx()


def ip_not_exists(screen, screen_dims):
    screen.addstr(screen_dims[0] / 2 - 2, screen_dims[1] / 2 - 26,
                  "No valid IP found. Please complete the previous step", curses.A_BOLD | curses.color_pair(3))
    screen.addstr(screen_dims[0] / 2 - 1, screen_dims[1] / 2 - 22,
              "Press p to input ip address, or 'm' for menu", curses.color_pair(5))
    while key_press not in (109, 112):  # 109 == m, 112 == p
        key_press = screen.getch()
    if key_press == 109:
        display_menu(screen, status_window)
    elif key_press == 112:
        menu_ping_ldap_ip(screen)


def basic_ldap_menu_success(screen, conn_info, screen_dims):
    var_dict["conn_info"] = conn_info
    screen.addstr(screen_dims[0] / 2 - 6, screen_dims[1] / 2 - len(conn_info['message']) / 2,
                  conn_info['message'],
                  curses.color_pair(6) | curses.A_BOLD)
    menu_options[1] = u"2. Check Connection to LDAP (URL) ✓"
    menu_color[1] = curses.color_pair(7)
    screen.addstr(screen_dims[0] / 2 - 5, screen_dims[1] / 2 - 25,
                  "Press 'n' to move on to next step, or 'm' for menu.")
    character = screen.getch()
    while character != 109:
        character = screen.getch()
    if character == 109:  # 109 == m
        display_menu(screen, status_window)


def basic_ldap_menu_fail(screen, conn_info, screen_dims):
    screen.addstr(screen_dims[0] / 2 - 6, screen_dims[1] / 2 - len(conn_info['message']) / 2,
                  conn_info['message'],
                  curses.color_pair(3) | curses.A_BOLD)
    screen.addstr(screen_dims[0] / 2 - 5, screen_dims[1] / 2 - 18,
              "Press 'r' to retry, or 'm' for menu.")
    char = screen.getch()
    while char not in (109, 114):
        char = screen.getch()
    if char == 109:
        display_menu(screen, status_window)
    elif char == 114:
        menu_check_ldap_connection_basic(screen)


def adv_ldap_setup_prompts(screen, max_yx):
    host_ip = configuration_dict["url"]
    temp_str = my_raw_input(screen, max_yx[0] / 2 - 4, max_yx[1] / 2 - 22,
                            "Please enter the port number. Default is 389.")
    while not temp_str.isdigit():
        screen.clear()
        temp_str = my_raw_input(screen, max_yx[0] / 2 - 4, max_yx[1] / 2 - 22,
                                "Input entered is not a valid port number. Please retry.")
    port_numb = int(temp_str)

    userpw_y_or_n = prompt_char_input(screen, max_yx[0] / 2 - 2, max_yx[1] / 2 - 22,
                                      "Does LDAP server require User/Pass? [y/n]", ('y', 'n'))
    if userpw_y_or_n == 'y':
        user_name = my_raw_input(screen, max_yx[0] / 2, max_yx[1] / 2 - 22, "Please input your username.")
        # if want password hidden as "*" change my_raw_input to my_pw_input
        pass_wd = my_raw_input(screen, max_yx[0] / 2 + 2, max_yx[1] / 2 - 22,
                               "Please type your password and hit enter.")
        tls_y_coord = max_yx[0] / 2 + 4
    else:
        user_name = ""
        pass_wd = ""
        tls_y_coord = max_yx[0] / 2

    tls_y_or_n = prompt_char_input(screen, tls_y_coord, max_yx[1] / 2 - 22,
                                   "Is TLS enabled? Enter [y/n]", ('y', 'n'))
    if tls_y_or_n == 'n':
        tls_cert_path = None
    else:
        tls_cert_path = my_raw_input(screen, max_yx[0] / 2 + 6, max_yx[1] / 2 - 22,
                                     "Please enter the path of the TLS certificate.")
        while not os.path.isfile(tls_cert_path):
            screen.addstr(max_yx[0] / 2 + 6, max_yx[1] / 2 - 22,
                          "                                              ")
            screen.addstr(max_yx[0] / 2 + 7, max_yx[1] / 2 - 22,
                          ">                                              ")
            tls_cert_path = my_raw_input(screen, max_yx[0] / 2 + 6, max_yx[1] / 2 - 22,
                                         "File not found. Please try again.")
    return [host_ip, port_numb, user_name, pass_wd, tls_y_or_n, tls_cert_path]


def adv_ldap_success(screen, conn_info, max_yx):
    var_dict["conn_info"] = conn_info
    screen.addstr(max_yx[0] / 2 - 7, max_yx[1] / 2 - len(conn_info['message']) / 2,
                  conn_info['message'],
                  curses.color_pair(6) | curses.A_BOLD)
    menu_options[2] = u"3. Check Connection to LDAP (URL, User/Pass, SSL/TLS) ✓"
    menu_color[2] = curses.color_pair(7)
    screen.addstr(max_yx[0] / 2 - 6, max_yx[1] / 2 - 25,
                  "Press 'n' to move on to next step, or 'm' for menu.",
                  curses.color_pair(3) | curses.A_BOLD)
    character = screen.getch()
    while character != 109:
        character = screen.getch()
    if character == 109:  # 109 == m
        display_menu(screen, status_window)


def adv_ldap_fail(screen, conn_info, max_yx):
    screen.addstr(max_yx[0] / 2 - 7, max_yx[1] / 2 - len(conn_info['message']) / 2,
                  conn_info['message'],
                  curses.color_pair(3) | curses.A_BOLD)

    screen.addstr(max_yx[0] / 2 - 6, max_yx[1] / 2 - 18,
                  "Press 'r' to retry, or 'm' for menu.")
    char = screen.getch()
    while char not in (109, 114):
        char = screen.getch()
    if char == 109:
        display_menu(screen, status_window)
    elif char == 114:
        menu_check_ldap_connection_adv(screen)


"""MAIN METHODS"""


def show_console_in_status_window():
    status_window_text_dimensions = status_window_text.getmaxyx()
    stat_win_half_y = status_window_text_dimensions[0]/2
    stat_win_half_x = status_window_text_dimensions[1]/2
    configuration_dict_yaml_str = yaml.dump(configuration_dict, stream=None, default_flow_style=False)
    configuration_dict_str = str(configuration_dict)
    status_window_text.addstr(0, 0, configuration_dict_yaml_str)


def menu_ping_ldap_ip(screen):
    """Displays a screen prompting user for IP address and then
    pings that IP address to see if it able to send a response."""
    screen_dims = setup_menu_call(screen)

    success = "Successfully pinged given IP address."
    fail = "Unsuccessfully pinged given IP address."
    prompt_ip_string = "Please Enter the IP Address of the LDAP server."
    ip_string = my_raw_input(screen, screen_dims[0] / 2, screen_dims[1] / 2 - len(prompt_ip_string)/2,
                             prompt_ip_string)
    screen.addstr(screen_dims[0] / 2 - 5, screen_dims[1] / 2 - 12, "Attempting to ping IP...",
                  curses.color_pair(5) | curses.A_BLINK)
    screen.refresh()

    temp_bool = configTool.ping_LDAP_server(ip_string)
    if temp_bool == 1 and ip_string != "":
        screen.addstr(screen_dims[0] / 2 - 4, screen_dims[1] / 2 - len(success) / 2,
                      success, curses.color_pair(6))
        screen.addstr(screen_dims[0] / 2 - 3, screen_dims[1] / 2 - 26,
                      "This IP will automatically be used in the next steps.", curses.color_pair(4))
        screen.addstr(screen_dims[0] / 2 - 2, screen_dims[1] / 2 - 25,
                      "Press 'n' to move on to next step, or 'm' for menu.")
        menu_options[0] = u"1. Ping LDAP Server IP ✓"
        menu_color[0] = curses.color_pair(7)
        configuration_dict["url"] = ip_string
    elif temp_bool == -1:
        screen.addstr(screen_dims[0] / 2 - 4, screen_dims[1] / 2 - 30,
                      "Invalid Hostname or IP. Press 'r' to retry, or 'm' for menu.", curses.color_pair(3))
    else:
        screen.addstr(screen_dims[0] / 2 - 4, screen_dims[1] / 2 - len(fail) / 2, fail, curses.color_pair(3))
        screen.addstr(screen_dims[0] / 2 - 3, screen_dims[1] / 2 - 23,
                      "Press 'r' to retry this step, or 'm' for menu.")
    temp_char = screen.getch()
    while temp_char not in (110, 109, 114):  # 109 = 'm', 110 = 'n', 114 = 'r'
        temp_char = screen.getch()
    if temp_char == 109:
        display_menu(screen, status_window)
    elif temp_char == 110:
        menu_check_ldap_connection_basic(screen)
    elif temp_char == 114:
        menu_ping_ldap_ip(screen)


def menu_check_ldap_connection_basic(screen):
    """The method that handles the 'Check Connections to LDAP Server' option."""
    screen_dims = setup_menu_call(screen)
    if configuration_dict["url"] == "none":
        ip_not_exists(screen, screen_dims)
    else:
        y_n = prompt_char_input(screen, screen_dims[0] / 2 - 4, screen_dims[1] / 2 - 26,
                                "Valid IP has been found, would you like to use this? [y/n]", ('y', 'n'))
        screen.clear()
        if y_n == 'y':
            host_ip = configuration_dict["url"]
            temp_str = my_raw_input(screen, screen_dims[0] / 2 - 3, screen_dims[1] / 2 - 22,
                                    "Please enter the port number. Default is 389.")
            while not temp_str.isdigit():
                screen.clear()
                temp_str = my_raw_input(screen, screen_dims[0] / 2 - 3, screen_dims[1] / 2 - 30,
                                        "Input entered is not a valid port number. Please retry.")
            port_numb = int(temp_str)
            screen.addstr(screen_dims[0] / 2 - 7, screen_dims[1] / 2 - 18, "Attempting to connect to LDAP server...",
                          curses.color_pair(5))
            screen.refresh()

            conn_info = configTool.connect_LDAP_server_basic(host_ip, port_numb)
            if conn_info['exit_status'] == 1:
                basic_ldap_menu_success(screen, conn_info, screen_dims)
            else: # error occurred during ldap ping
                basic_ldap_menu_fail(screen, conn_info, screen_dims)
        else:
            menu_ping_ldap_ip(screen)


def menu_check_ldap_connection_adv(screen):
    max_yx = setup_menu_call(screen)
    if configuration_dict["url"] == "none":
        ip_not_exists(screen, max_yx)
    else:
        y_n = prompt_char_input(screen, max_yx[0] / 2 - 4, max_yx[1] / 2 - 26,
                                "Valid IP has been found, would you like to use this? [y/n]", ('y', 'n'))
        screen.clear()
        if y_n == 'y':
            adv_ldap_inputs = adv_ldap_setup_prompts(screen, max_yx)
            host_ip = adv_ldap_inputs[0]
            port_numb = adv_ldap_inputs[1]
            user_name = adv_ldap_inputs[2]
            pass_wd = adv_ldap_inputs[3]
            tls_y_or_n = adv_ldap_inputs[4]
            tls_cert_path = adv_ldap_inputs[5]
            screen.addstr(max_yx[0] / 2 - 8, max_yx[1] / 2 - 18, "Attempting to connect to LDAP server...",
                          curses.color_pair(5))
            conn_info = configTool.connect_LDAP_server(host_ip, port_numb, user_name, pass_wd, tls_y_or_n,
                                                       tls_cert_path)
            if conn_info['exit_status'] == 1:
                adv_ldap_success(screen, conn_info, max_yx)
            else:  # error occurred during ldap ping
                adv_ldap_fail(screen, conn_info, max_yx)
        else:
            menu_ping_ldap_ip(screen)


def menu_get_server_info(screen):
    """Displays server information on screen.
    Currently needs fullscreen in order to print everything, but later will parse information."""
    screen_dims = setup_menu_call(screen)
    if var_dict["conn_info"] == "none":
        screen.addstr(screen_dims[0] / 2, screen_dims[1] / 2 - 23, "No LDAP server found. Press 'm' to go to menu.",
                      curses.color_pair(3) | curses.A_BOLD)
        screen.getch()
        display_menu(screen, status_window)
    else:
        menu_options[3] = u"4. Get Server Information ✓"
        menu_color[3] = curses.color_pair(7)
        conn_info = var_dict["conn_info"]
        server = conn_info["server"]
        server_info_dict = configTool.retrieve_server_info(server)
        server_info = server_info_dict["info"]
        server_info_str = str(server_info)
        num_spaces = [" "]*(screen_dims[1]/2 - 8)
        str_spaces = ''.join(num_spaces)
        screen.addstr(0,0, server_info_str + "\n" + str_spaces + "Press m to go to the menu.")
        c = screen.getch()
        while c != (109):
            c = screen.getch()
        if c == 109:
            display_menu(screen, status_window)


def menu_check_ldap_suffix(screen):
    screen_dims = setup_menu_call(screen)
    if var_dict["conn_info"] == "none":
        screen.addstr(screen_dims[0] / 2, screen_dims[1] / 2 - 8, "No LDAP server found. Press 'm' to go to menu.")
        screen.getch()
        display_menu(screen, status_window)
    else:
        conn_info = var_dict["conn_info"]
        conn = conn_info['conn']
        prompt_str = "Please enter the base dn. (i.e. dc=openstack,dc=org)"
        base_dn = my_raw_input(screen, screen_dims[0]/2, screen_dims[1]/2 - len(prompt_str)/2, prompt_str)
        results = configTool.check_LDAP_suffix(conn, base_dn)
        if results["exit_status"] == 1:
            configuration_dict["suffix"] = base_dn
            menu_options[4] = u"5. Check LDAP Suffix ✓"
            menu_color[4] = curses.color_pair(7)
            message_color = 6
        else:
            message_color = 3
        screen.addstr(screen_dims[0] / 2 - 2, screen_dims[1] / 2 - len(results['message']) / 2, results['message'],
                      curses.color_pair(message_color) | curses.A_BOLD)
        c = screen.getch()
        while c != (109):
            c = screen.getch()
        if c == 109:
            display_menu(screen, status_window)


def menu_show_list_user_object_classes(screen):
    screen_dims = setup_menu_call(screen)
    if var_dict["conn_info"] == "none" or configuration_dict["suffix"] == "none":
        screen.addstr(screen_dims[0] / 2, screen_dims[1] / 2 - 8, "No LDAP server found. Press 'm' to go to menu.")
        screen.getch()
        display_menu(screen, status_window)
    else:
        conn_info = var_dict["conn_info"]
        conn = conn_info['conn']
        base_dn = configuration_dict["suffix"]
        user_id_attribute = my_raw_input(screen, screen_dims[0]/2, screen_dims[1]/2, "What is the user id attribute?")
        configuration_dict["user_id_attribute"] = user_id_attribute
        return_values = configTool.list_user_related_OC(conn, base_dn, user_id_attribute)
        if return_values['exit_status'] == 1:
            screen.addstr(screen_dims[0]/2 + 1, screen_dims[1]/2, str(return_values['objectclasses']))
        screen.getch()


def menu_check_user_tree_dn_show_users(screen):
    print("NEEDS IMPLEMENTATION")


def menu_get_specific_user(screen):
    print("NEEDS IMPLEMENTATION")


def menu_show_list_group_object_classes(screen):
    print("NEEDS IMPLEMENTATION")


def menu_check_group_tree_dn_show_groups(screen):
    print("NEEDS IMPLEMENTATION")


def menu_get_specific_group(screen):
    print("NEEDS IMPLEMENTATION")


def menu_additional_config_options(screen):
    print("NEEDS IMPLEMENTATION")


def menu_show_config(screen):
    print("NEEDS IMPLEMENTATION")


def menu_create_config(screen):
    print("NEEDS IMPLEMENTATION")


def display_menu(screen, status_window):
    """Displays the menu. Does most of the work for displaying options."""
    screen_dimensions = screen.getmaxyx()
    screen_half_y = screen_dimensions[0]/2
    screen_half_x = screen_dimensions[1]/2
    screen.nodelay(0)
    screen.clear()
    screen.box()
    status_window.box()
    show_console_in_status_window()
    status_window.refresh()
    screen.refresh()

    menu_selection = -1
    option_num = 0
    while menu_selection < 0:
        menu_highlighting = [0] * 15 # number of menu options
        menu_highlighting[option_num] = curses.A_STANDOUT
        screen.addstr(screen_half_y - 9, screen_half_x - 11,
                      "LDAP Configuration Menu", curses.A_UNDERLINE | curses.color_pair(1) | curses.A_BOLD)
        screen.addstr(screen_half_y - 6, screen_half_x - 25,
                      menu_options[0].encode("utf-8"), menu_highlighting[0] | menu_color[0])
        screen.addstr(screen_half_y - 5, screen_half_x - 25,
                      menu_options[1].encode("utf-8"), menu_highlighting[1] | menu_color[1])
        screen.addstr(screen_half_y - 4, screen_half_x - 25,
                      menu_options[2].encode("utf-8"), menu_highlighting[2] | menu_color[2])
        screen.addstr(screen_half_y - 3, screen_half_x - 25,
                      menu_options[3].encode("utf-8"), menu_highlighting[3] | menu_color[3])
        screen.addstr(screen_half_y - 2, screen_half_x - 25,
                      menu_options[4].encode("utf-8"), menu_highlighting[4] | menu_color[4])
        screen.addstr(screen_half_y - 1, screen_half_x - 25,
                      menu_options[5].encode("utf-8"), menu_highlighting[5] | menu_color[5])
        screen.addstr(screen_half_y + 0, screen_half_x - 25,
                      menu_options[6].encode("utf-8"), menu_highlighting[6] | menu_color[6])
        screen.addstr(screen_half_y + 1, screen_half_x - 25,
                      menu_options[7].encode("utf-8"), menu_highlighting[7] | menu_color[7])
        screen.addstr(screen_half_y + 2, screen_half_x - 25,
                      menu_options[8].encode("utf-8"), menu_highlighting[8] | menu_color[8])
        screen.addstr(screen_half_y + 3, screen_half_x - 25,
                      menu_options[9].encode("utf-8"), menu_highlighting[9] | menu_color[9])
        screen.addstr(screen_half_y + 4, screen_half_x - 25,
                      menu_options[10].encode("utf-8"), menu_highlighting[10] | menu_color[10])
        screen.addstr(screen_half_y + 5, screen_half_x - 25,
                      menu_options[11].encode("utf-8"), menu_highlighting[11] | menu_color[11])
        screen.addstr(screen_half_y + 6, screen_half_x - 25,
                      menu_options[12].encode("utf-8"), menu_highlighting[12] | menu_color[12])
        screen.addstr(screen_half_y + 7, screen_half_x - 25,
                      menu_options[13].encode("utf-8"), menu_highlighting[13] | menu_color[13])
        screen.addstr(screen_half_y + 8, screen_half_x - 25, "15. Exit",
                      menu_highlighting[14] | curses.color_pair(3))
        screen.refresh()

        key_press = screen.getch()
        if key_press == curses.KEY_UP:
            option_num = (option_num - 1) % 15
        elif key_press == curses.KEY_DOWN:
            option_num = (option_num + 1) % 15
        elif key_press == ord('\n'):
            menu_selection = option_num
            if option_num == 0:
                menu_ping_ldap_ip(screen)
            elif option_num == 1:
                menu_check_ldap_connection_basic(screen)
            elif option_num == 2:
                menu_check_ldap_connection_adv(screen)
            elif option_num == 3:
                menu_get_server_info(screen)
            elif option_num == 4:
                menu_check_ldap_suffix(screen)
            elif option_num == 5:
                menu_show_list_user_object_classes(screen)
            elif option_num == 14:
                sys.exit(0)
            else:
                display_menu(screen, status_window)
    curses.curs_set(1)
curses.wrapper(show_instructions)
curses.endwin()
