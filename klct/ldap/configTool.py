import os
import ssl
import subprocess
import socket
import sys
import ldap3
from ldap3 import Server, Connection, ALL


def check_valid_IP(host_name):
    """Checks if the given hostName is a valid IP address.
    Return 1 if valid, 0 if invalid.
    note: only checks for valid ipv4 IPs
          need to implement validation for IPV6
    """
    try:
        socket.inet_aton(host_name)
        return 1
    except socket.error:
        pass
    try:
        socket.inet_pton(socket.AF_INET6, host_name)
        return 1
    except socket.error:
        return 0


def setup_connection(host_name, port_number, user_name, password, want_tls, tls_cert_path):
    """Sets up a connection given the parameters.
    Note: unbind the returned connection when finished using socket
    Note: need to find a way to check validation of certificate, eg. expiration, etc
    """
    return_values = {'exit_status': 0, 'message': [], 'error': [], 'server': [], 'conn': []}
    if port_number is None and want_tls == 'n':
        port_number = 389
    elif port_number is None and want_tls == 'y':
        port_number = 636
    try:
        if want_tls == 'n':
            return_values['server'] = Server(host_name, port=port_number, get_info=ALL)
        else:
            tls_object = ldap3.Tls(ca_certs_file=tls_cert_path, validate=ssl.CERT_REQUIRED)
            return_values['server'] = Server(host_name, port=port_number, use_ssl=True, tls=tls_object, get_info=ALL)
        #print("\nTrying to connect...")
        #print(server)
        return_values['conn'] = Connection(return_values['server'], version=3, user=user_name, password=password)
        #print("connection started")
        #conn.open() #bind implies open
        if not return_values['conn'].bind():
            return 0, "bind failed", return_values['conn'].results
        if want_tls == 'y':
            #print("starting tls\n")
            #conn.open()
            return_values['conn'].start_tls()
        #print(conn)
        return_values['exit_status'] = 1
        return_values['message'] = "Successfully connected!"
    except ldap3.LDAPSocketOpenError as err:
        return_values['message'] = "Failed to connect due to invalid socket."
        return_values['error'] = err
    except ldap3.LDAPInvalidPortError as err:
        return_values['message'] = "Invalid Port"
        return_values['error'] = err
    except AttributeError as err:
        return_values['message'] = "Invalid log in info"
        return_values['error'] = err
    except ldap3.LDAPPasswordIsMandatoryError as err:
        return_values['message'] = "Please enter a password"
        return_values['error'] = err
    except:
        return_values['message'] = "Failed to connect due to unknown reasons"
        return_values['error'] = sys.exc_info()[1]
    return return_values


def create_filter():
    return "filter goes here"


def ping_LDAP_server(host_name):
    """Checks if the given hostName is valid, and pings it.
    """
    try:
        host_name = socket.gethostbyname(host_name)
    except socket.gaierror:
        pass

    is_valid = check_valid_IP(host_name)
    if not is_valid:
        return -1
    response = None

    with open(os.devnull, "w"):
        try:
            subprocess.check_output(["ping", "-c", "1", host_name], stderr=subprocess.STDOUT, universal_newlines=True)
            response = 1
        except subprocess.CalledProcessError:
            response = 0
    return response


def connect_LDAP_server_basic(host_name, port_number):
    """Attempts to connect to the provided hostName and port number, default port is 389 if none provided.
    """
    conn_info = setup_connection(host_name, port_number, "", "", 'n', "")
    if conn_info['exit_status'] == 1:
        pass #conn_info['conn'].unbind() front end will unbind for now
    return conn_info


def connect_LDAP_server(host_name, port_number, user_name, password, want_tls, tls_cert_path):
    """Attempts to connect to the provided hostName and port number, default port is 389 if none provided, using the provided user name and pass.
    Note: tls not working
    """
    conn_info = setup_connection(host_name, port_number, user_name, password, want_tls, tls_cert_path)
    if conn_info['exit_status'] == 1:
        pass #conn_info['conn'].unbind() front end will unbind for now
    return conn_info


def retrieve_server_info(server):
    """Retrieves the information related to the server passed in
    """
    dict = {'info': server.info, 'schema': server.schema}
    return dict


def check_LDAP_suffix(conn, base_dn):
    """Checks that the given base_dn is the correct suffix for the given connection
    """
    assert conn.closed is not True
    #print(conn)
    if conn.search(search_base=base_dn, search_filter='(cn=admin)') is True:
        return {'exit_status': 1, 'message': "The given base DN is correct"}
    else:
        return {'exit_status': 0, 'message': "The given base DN is not correct"}


def list_user_related_OC(conn, base_dn, user_name):
    """Returns a list of the object classes related to the given user.
    """
    assert conn.closed is not True
    search_filter = create_filter()
    if conn.search(search_base=base_dn, search_filter=search_filter, attributes=['objectclass']) is True:
        return {'exit_status': 1, 'objectclasses': conn.entries[0].objectclass.raw_values}
    else:
        return {'exit_status': 0, 'objectclasses': None}


def list_users(conn, base_dn, user_name, limit):
    """Lists the users, up to the limit
    """
    assert conn.closed is not True
    if limit is None:
        limit = 3
    search_filter = create_filter()
    if conn.search(search_base=user_name + ',' + base_dn, search_filter=search_filter, attributes=[], size_limit=limit) is True:
        return {'exit_status': 1, 'users': conn.entries}
    else:
        return {'exit_status': 0, 'users': None}


def get_user(conn, base_dn, user_name, name):
    """Returns a specific user
    """
    assert conn.closed is not True
    search_filter = create_filter()
    if conn.search(search_base=user_name + ',' + base_dn, search_filter=search_filter, attributes=[]) is True:
        return {'exit_status': 1, 'user': conn.entries}
    else:
        return {'exit_status': 0, 'user': None}

def list_group_related_OC():
    print("needs to be implemented")


def list_groups():
    print("needs to be implemented")


def get_group():
    print("needs to be implemented")


def show_config():
    print("needs to be implemented")


def save_config():
    print("needs to be implemented")
