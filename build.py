from pybuilder.core import use_plugin, init
import inspect, os, sys

my_location = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.append(my_location)
sys.path.append(my_location + '/../quant_container')

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.coverage")
use_plugin("python.install_dependencies")
use_plugin("python.distutils")
#use_plugin("python.flake8") # what is that?

name = "msq-domain"
default_task = "publish"

@init
def initialize(project):
    project.build_depends_on('cloudpickle')
    project.build_depends_on('aiokafka')
    project.build_depends_on('kafka')
    project.build_depends_on('kafka-python')
    project.build_depends_on('mockito')

    project.set_property('dir_source_main_python','mosaicsmartdata')
    project.set_property('dir_source_unittest_python', 'unit_tests')
    project.set_property('dir_source_main_scripts', 'scripts')
