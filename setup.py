import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# Don't import module here, since deps may not be installed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "hanzoanalytics"))
from version import VERSION  # noqa: E402

long_description = """
Hanzo Insights is developer-friendly, self-hosted product analytics.
hanzoanalytics is the python package.

This package requires Python 3.10 or higher.
"""

setup(
    name="hanzoanalytics",
    version=VERSION,
    url="https://github.com/hanzoai/insights",
    author="Hanzo AI",
    author_email="hey@hanzo.ai",
    maintainer="Hanzo AI",
    maintainer_email="hey@hanzo.ai",
    license="MIT License",
    description="Integrate Hanzo Insights into any python application.",
    long_description=long_description,
)
