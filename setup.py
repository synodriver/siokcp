# -*- coding: utf-8 -*-
import os
import re
import sys
from collections import defaultdict

from Cython.Build import cythonize
from Cython.Compiler.Version import version as cython_version
from packaging.version import Version
from setuptools import Extension, find_packages, setup
from setuptools.command.build_ext import build_ext

BUILD_ARGS = defaultdict(lambda: ["-O3", "-g0"])

for compiler, args in [
    ("msvc", ["/EHsc", "/DHUNSPELL_STATIC", "/Oi", "/O2", "/Ot"]),
    ("gcc", ["-O3", "-g0"]),
]:
    BUILD_ARGS[compiler] = args


class build_ext_compiler_check(build_ext):
    def build_extensions(self):
        compiler = self.compiler.compiler_type
        args = BUILD_ARGS[compiler]
        for ext in self.extensions:
            ext.extra_compile_args = args
        super().build_extensions()


def has_option(name: str) -> bool:
    if name in sys.argv[1:]:
        sys.argv.remove(name)
        return True
    name = name.strip("-").upper()
    if os.environ.get(name, None) is not None:
        return True
    return False


macro_base = []
if (
    sys.version_info > (3, 13, 0)
    and hasattr(sys, "_is_gil_enabled")
    and not sys._is_gil_enabled()
):
    print("build nogil")
    macro_base.append(
        ("Py_GIL_DISABLED", "1"),
    )

compiler_directives = {
    "cdivision": True,
    "embedsignature": True,
    "boundscheck": False,
    "wraparound": False,
}


if Version(cython_version) >= Version("3.1.0a0"):
    compiler_directives["freethreading_compatible"] = True

extensions = [
    Extension(
        "siokcp._kcp",
        ["siokcp/_kcp.pyx", "./kcp/ikcp.c"],
        include_dirs=[f"./kcp"],
        library_dirs=[f"./kcp"],
        define_macros=macro_base,
    ),
]


def get_dis():
    with open("README.markdown", "r", encoding="utf-8") as f:
        return f.read()


def get_version() -> str:
    path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "siokcp", "__init__.py"
    )
    with open(path, "r", encoding="utf-8") as f:
        data = f.read()
    result = re.findall(r"(?<=__version__ = \")\S+(?=\")", data)
    return result[0]


packages = find_packages(exclude=("test", "tests.*", "test*"))


def main():
    version: str = get_version()
    dis = get_dis()
    setup(
        name="siokcp",
        version=version,
        url="https://github.com/synodriver/siokcp",
        packages=packages,
        keywords=["kcp"],
        description="sans-io style kcp",
        long_description_content_type="text/markdown",
        long_description=dis,
        author="synodriver",
        author_email="diguohuangjiajinweijun@gmail.com",
        python_requires=">=3.6",
        setup_requires=["Cython>=3.0.9"],
        license="BSD",
        classifiers=[
            "Development Status :: 4 - Beta",
            "Operating System :: OS Independent",
            "License :: OSI Approved :: BSD License",
            "Programming Language :: C",
            "Programming Language :: Cython",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
            "Programming Language :: Python :: 3.13",
            "Programming Language :: Python :: Implementation :: CPython",
        ],
        include_package_data=True,
        zip_safe=False,
        cmdclass={"build_ext": build_ext_compiler_check},
        ext_modules=cythonize(extensions, compiler_directives=compiler_directives),
    )


if __name__ == "__main__":
    main()