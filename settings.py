KF2_SERVER_DIR="o:/kf2/server"
HTTP_LISTEN_PORT=8008
HTTP_LISTEN_ADDRESS="localhost"
SPLIT_MAP_DIFFICULTY=False


USERNAME = "user"
PASSWORD = "wsmapadmin2103"



def config_dir():
    return KF2_SERVER_DIR + "/KFGame/Config"

def cache_dir():
    return KF2_SERVER_DIR + "/KFGame/Cache"

def map_dir():
    return KF2_SERVER_DIR + "/KFGame/BrewedPC/Maps"

def idlist_file():
    return config_dir() + "/PCServer-KFEngine.ini"

def maplist_file():
    return config_dir() + "/PCServer-KFGame.ini"

