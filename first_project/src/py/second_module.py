from first_project.src.py.first_module import special_hello_world



if __name__ == "__main__":
    # https://stackoverflow.com/questions/48746494/how-to-use-a-packed-python-package-without-installing-it
    from sys import path as sys_path
    from os import path as os_path
    sys_path.append(os_path.join(os_path.expanduser("~"), 'Projects/FirstProject'))

    special_hello_world()
