from utils.mcp import Server
from tools import *
# from prompt import *

mcp = Server().mcp


def main():
    mcp.run()


# Run the server
if __name__ == "__main__":
    main()
