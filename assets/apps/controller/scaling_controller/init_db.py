import sqlite3

import os

from scaling_controller.consts import DB_PATH, CREATE_METRICS_TABLE


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    con = sqlite3.connect(DB_PATH)

    # Create the table
    con.execute(CREATE_METRICS_TABLE)
    con.close()


if __name__ == '__main__':
    main()
