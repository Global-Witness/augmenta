from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop
import subprocess
import sys

def install_playwright_deps():
    print("Installing Playwright browsers...")
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    except subprocess.CalledProcessError as e:
        print(f"Failed to install Playwright browsers: {e}")
        raise

class PostInstallCommand(install):
    def run(self):
        install.run(self)
        install_playwright_deps()

class PostDevelopCommand(develop):
    def run(self):
        develop.run(self)
        install_playwright_deps()

setup(
    cmdclass={
        'install': PostInstallCommand,
        'develop': PostDevelopCommand,
    },
)