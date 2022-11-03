import os
import logging

logger = logging.getLogger(__name__)

def custom_move():
    dest_dir = "/home/docker"
    source_dir = "/home/dockerfake/fake/"
    sub_directories = os.listdir(source_dir)
    for sub_dir in sub_directories:
        print(f"sudo cp -a {source_dir}{sub_dir} {dest_dir}/{sub_dir}")


def special_hello_world():
    print(f"{__name__}: special hello world!")
    print(f"{__name__}: new message!")


if __name__ == "__main__":
    special_hello_world()
