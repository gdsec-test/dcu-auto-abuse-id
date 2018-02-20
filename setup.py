from setuptools import setup, find_packages
from pip.req import parse_requirements


# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements('requirements.txt', session=False)
testing_reqs = parse_requirements('test_requirements.txt', session=False)

# reqs is a list of requirement
# e.g. ['django==1.5.1', 'mezzanine==1.4.6']
reqs = [str(ir.req) for ir in install_reqs]
test_reqs = [str(ir.req) for ir in testing_reqs]

setup(
    name='auto_abuse_id',
    version='1.0',
    description='Deals with automated detection of abusive content',
    author='DCU',
    author_email='dcueng@godaddy.com',
    url='https://github.secureserver.net/ITSecurity/auto_abuse_id',
    # packages=packages,
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=reqs,
    tests_require=test_reqs,
    test_suite="nose.collector")
