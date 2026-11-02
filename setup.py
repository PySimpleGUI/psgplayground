import os
import re
import setuptools

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = 'https://raw.githubusercontent.com/PySimpleGUI/psgplayground/main/'      # where PyPI can fetch the README's images
WEB = 'https://github.com/PySimpleGUI/psgplayground/blob/main/'               # where PyPI readers open the README's markdown links (GitHub redirects folders)
VERSION = re.search(r"^VERSION = '([^']+)'", open(os.path.join(HERE, "psgplayground", "playground.py"), encoding="utf-8").read(), re.M).group(1)     # one version number: the Toybox's


def readme():
    try:
        with open("README.md", encoding="utf-8") as f:
            text = re.sub(r'((?:src|href)=")(?!https?://|#|mailto:)', r'\g<1>' + RAW, f.read())       # repo-relative images and links work on GitHub, not on PyPI - point them at GitHub
            return re.sub(r'(!?\[[^\]]*\]\()(?!https?://|#|mailto:)([^)\s]+?)/?\)', lambda m: m[1] + (RAW if m[1][0] == '!' else WEB) + m[2] + ')', text)   # markdown ](links) too
    except IOError:
        return ""


setuptools.setup(
    name="psgplayground",
    version=VERSION,
    author="PySimpleGUI",
    install_requires=["PySimpleGUI>=6.4"],
    description="PySimpleGUI Playground - the Toybox app browser and a collection of real PySimpleGUI desktop apps to run, read and take apart",
    long_description=readme(),
    long_description_content_type="text/markdown",
    keywords="GUI UI PySimpleGUI tkinter playground widgets MIDI",
    url="https://github.com/PySimpleGUI/psgplayground",
    packages=["psgplayground"],
    include_package_data=True,
    package_data={"psgplayground": ["catalog.json", "icons/*", "*/*.py", "*/*.pyw", "*/*.md", "*/*.png", "*/*/*.py", "*/*/*.pyw", "*/*/*.png"]},
    license="GNU Lesser General Public License v3 (LGPLv3)",
    python_requires=">=3.8",
    classifiers=(
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
        "Framework :: PySimpleGUI",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: User Interfaces",
    ),
    entry_points={"gui_scripts": ["psgplayground=psgplayground.playground:run"]},
)
