from install_service import install_service


def install_autostart():
    return install_service()


if __name__ == "__main__":
    print(install_autostart())
