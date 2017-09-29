from pybuilder.core import use_plugin, init
import inspect, os, sys

# Don't delete these 3 lines: I comment them in to run pyb locally
# my_location = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# sys.path.append(my_location)
# sys.path.append(my_location + '/../quant_container/src')

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.install_dependencies")
use_plugin("python.distutils")
use_plugin('python.pycharm')

name = "msq-domain"
default_task = "publish"

@init
def initialize(project):
    project.depends_on('cloudpickle')
    project.depends_on('aiokafka',version = "==0.2.1")
    project.depends_on('kafka',version = "==1.3.1")
    project.depends_on('mockito')

    project.set_property('dir_source_main_python','src')
    project.set_property('dir_source_unittest_python', 'unit_tests')
    project.set_property('dir_source_main_scripts', 'scripts')

    # without this, pybuilder only copies over *.py files
    project.include_directory('mosaicsmartdata/configuration', ['*.csv'])

@init(environments='test')
def set_properties_for_test(project):
    from aiostreams.config import QCConfigProvider
    QCConfigProvider().kafka_broker = 'kafka:9092'

    #project.version = '%s-%s' % (project.version, os.environ.get('BUILD_NUMBER', 0))
    # project.default_task = ['install_dependencies', 'package', 'verify']
    #project.set_property('install_dependencies_use_mirrors', False)
    #project.get_property('distutils_commands').append('bdist_rpm')
    #project.set_property('teamcity_output', True)
