import argparse
import os
import server


def main():
    parser = argparse.ArgumentParser(description="Codr Runner MCP Server")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-i", "--image", dest="image", type=str, help="image name")
    group.add_argument("-n", "--name", dest="name", type=str, help="container name")
    group.add_argument(
        "--host", "--base_url", dest="base_url", type=str, help="docker host"
    )

    args = parser.parse_args()

    if args.name is None and args.image is None:
        raise ValueError("Must set up a image or container.")

    if args.base_url:
        os.environ["DOCKER_HOST"] = args.base_url

    server.system_args = vars(args)
    server.mcp.run()


# 5. Make the server runnable
if __name__ == "__main__":
    main()
